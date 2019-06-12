# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 14:06:48 2019

@author: HaanRJ
"""

import geojson
import numpy as np
from shapely import geometry
from copy import deepcopy
import modelInterface as D3D


def determine_dikes(hexagons):
    for feature in hexagons.features:
        if feature.properties["z"] >= 4:
            shape = geometry.asShape(feature.geometry)
            y_hex = shape.centroid.y
            if y_hex >= 0:
                feature.properties["north_dike"] = True
                feature.properties["south_dike"] = False
            else:
                feature.properties["north_dike"] = False
                feature.properties["south_dike"] = True
        else:
            feature.properties["north_dike"] = False
            feature.properties["south_dike"] = False
    return hexagons


def determine_channel(hexagons):
    for feature in hexagons.features:
        if feature.properties["z"] == 0:
            next_hexagon = hexagons[feature.id + 1]
            if next_hexagon.properties["z"] == 0:
                feature.properties["main_channel"] = True
                feature.properties["north_side_channel"] = True
                feature.properties["south_side_channel"] = False
            else:
                feature.properties["main_channel"] = True
                feature.properties["north_side_channel"] = False
                feature.properties["south_side_channel"] = True
        else:
            feature.properties["main_channel"] = False
            feature.properties["north_side_channel"] = False
            feature.properties["south_side_channel"] = False
    return hexagons


def get_channel(hexagons):
    hexagons_copy = deepcopy(hexagons)
    channel = []
    for feature in hexagons_copy.features:
        if feature.properties["main_channel"]:
            channel.append(feature)
    channel = geojson.FeatureCollection(channel)
    for i, feature in enumerate(channel.features):
        feature.id = i
    return channel


def create_structures(hexagons):
    """
    Results are better with 59 degrees for some reason that I cannot figure
    out yet.
    """
    sin = np.sin(np.deg2rad(60))
    cosin = np.cos(np.deg2rad(60))
    height = 0.0
    x_dist = 0.0
    y_dist = 0.0
    groyne_dist = 0.0
    structures = []
    for feature in hexagons.features:
        height = abs(height)
        groyne_dist = abs(groyne_dist)
        edge = False
        west_edge = False
        east_edge = False
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            # determine hexagon size and reusable variables for other hexagons
            # only for the first hexagon
            line = list(geojson.utils.coords(feature.geometry))
            maxy = 0.0
            for x, y in line:
                y = abs(y)
                if y > maxy:
                    maxy = y
            height = (maxy - abs(y_hex))
            x_dist = sin * height
            y_dist = cosin * height
        # Ideally would also want to do this with a try/except KeyError, but -1
        # index would find a hexagon
        if feature.id == 0 or feature.id == 1:
            edge = True
            west_edge = True
        else:
            left_hex = hexagons[feature.id - 2]
            shape = geometry.asShape(left_hex.geometry)
            y_hex_left = shape.centroid.y
        try:
            right_hex = hexagons[feature.id + 2]
            shape = geometry.asShape(right_hex.geometry)
            y_hex_right = shape.centroid.y
        except KeyError:
            edge = True
            east_edge = True
        if not edge:
            if y_hex < y_hex_left:
                hex_left_north = True
            else:
                hex_left_north = False
            if y_hex < y_hex_right:
                hex_right_north = True
            else:
                hex_right_north = False
        else:
            if west_edge:
                if y_hex < y_hex_right:
                    hex_left_north = False
                    hex_right_north = True
                else:
                    hex_left_north = True
                    hex_right_north = False
            if east_edge:
                if y_hex < y_hex_left:
                    hex_left_north = True
                    hex_right_north = False
                else:
                    hex_left_north = False
                    hex_right_north = True
        mid_point = [x_hex, y_hex]
        if hex_left_north and hex_right_north:
            # LTD shape: high to high: \_/
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            right_point = [x_top_left, y_top_left]
        elif hex_left_north and not hex_right_north:
            # LTD shape high to low: `-_
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex - y_dist
            right_point = [x_top_left, y_top_left]
        elif not hex_left_north and hex_right_north:
            # LTD shape low to high: _-`
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex + y_dist
            right_point = [x_top_left, y_top_left]
        else:
            # LTD shape low to high: /`\
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            right_point = [x_top_left, y_top_left]
        line = geojson.LineString([left_point, mid_point, right_point])
        ltd = geojson.Feature(id="LTD" + str(feature.id).zfill(2),
                              geometry=line)
        ltd.properties["active"] = False
        ltd.properties["crest_level"] = 0.0
        structures.append(ltd)

        groyne_dist = height * 0.25
        if feature.properties["south_side_channel"]:
            groyne_dist = groyne_dist * -1
            height = height * -1
        top_point = [x_hex, y_hex+height]
        bottom_point = [x_hex, y_hex+groyne_dist]
        line = geojson.LineString([top_point, bottom_point])
        groyne = geojson.Feature(id="groyne" + str(feature.id).zfill(2),
                                 geometry=line)
        groyne.properties["active"] = True
        groyne.properties["crest_level"] = 3.0
        structures.append(groyne)
    structures = geojson.FeatureCollection(structures)
    with open('structures_test.geojson', 'w') as f:
        geojson.dump(structures, f, sort_keys=True, indent=2)
    return structures


if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    hexagons = determine_dikes(hexagons)
    hexagons = determine_channel(hexagons)
    with open('hexagons_with_structures.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    channel = get_channel(hexagons)
    structures = create_structures(channel)
    D3D.geojson2pli(structures, name="structures_test")
