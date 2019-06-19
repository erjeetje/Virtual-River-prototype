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


def get_channel_old(hexagons, north_side=True):
    hexagons_copy = deepcopy(hexagons)
    channel = []
    for feature in hexagons_copy.features:
        if north_side:
            if feature.properties["north_side_channel"]:
                channel.append(feature)
        else:
            if feature.properties["south_side_channel"]:
                channel.append(feature)
    channel = geojson.FeatureCollection(channel)
    for i, feature in enumerate(channel.features):
        feature.id = i
    return channel


def create_groynes(hexagons):
    height = 0.0
    y_dist = 0.0
    groynes = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            line = list(geojson.utils.coords(feature.geometry))
            maxy = 0.0
            for x, y in line:
                y = abs(y)
                if y > maxy:
                    maxy = y
            height = (maxy - abs(y_hex))
            y_dist = height * 0.25
        if feature.properties["south_side_channel"]:
            y_dist = y_dist * -1
            height = height * -1
        else:
            y_dist = abs(y_dist)
            height = abs(height)
        top_point = [x_hex, y_hex+height]
        bottom_point = [x_hex, y_hex+y_dist]
        line = geojson.LineString([top_point, bottom_point])
        groyne = geojson.Feature(id="groyne" + str(feature.id).zfill(2), geometry=line)
        groyne.properties["active"] = True
        groynes.append(groyne)
    groynes = geojson.FeatureCollection(groynes)
    with open('groynes_test_line.geojson', 'w') as f:
        geojson.dump(groynes, f, sort_keys=True, indent=2)
    return groynes


def create_groynes_old(hexagons, north_side=True):
    height = 0.0
    y_dist = 0.0
    x_dist = 0.0
    groynes = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            line = list(geojson.utils.coords(feature.geometry))
            maxy = 0.0
            for x, y in line:
                y = abs(y)
                if y > maxy:
                    maxy = y
            height = (maxy - abs(y_hex))
            x_dist = (1/8) * height
            y_dist = height * 0.25
            if not north_side:
                y_dist = y_dist * -1
                height = height * -1
        left_point_top = [x_hex-x_dist, y_hex+height]
        right_point_top = [x_hex+x_dist, y_hex+height]
        right_point_bottom = [x_hex+x_dist, y_hex+y_dist]
        left_point_bottom = [x_hex-x_dist, y_hex+y_dist]
        polygon = geojson.Polygon([[left_point_top, right_point_top,
                                    right_point_bottom, left_point_bottom,
                                    left_point_top]])
        groyne = geojson.Feature(id=feature.id, geometry=polygon)
        groyne.properties["active"] = True
        groynes.append(groyne)
    groynes = geojson.FeatureCollection(groynes)
    if north_side:
        with open('groynes_test_north.geojson', 'w') as f:
            geojson.dump(groynes, f, sort_keys=True, indent=2)
    else:
        with open('groynes_test_south.geojson', 'w') as f:
            geojson.dump(groynes, f, sort_keys=True, indent=2)
    return groynes


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
    structures = []
    for feature in hexagons.features:
        """
        Ideally would also want to do this with a try/except KeyError, but -1
        index would find a hexagon.
        """
        edge = False
        west_edge = False
        east_edge = False
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0 or feature.id == 1:
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
        ltd = geojson.Feature(id="LTD" + str(feature.id).zfill(2), geometry=line)
        ltd.properties["active"] = False
        structures.append(ltd)
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            line = list(geojson.utils.coords(feature.geometry))
            maxy = 0.0
            for x, y in line:
                y = abs(y)
                if y > maxy:
                    maxy = y
            height = (maxy - abs(y_hex))
            y_dist = height * 0.25
        if feature.properties["south_side_channel"]:
            y_dist = y_dist * -1
            height = height * -1
        else:
            y_dist = abs(y_dist)
            height = abs(height)
        top_point = [x_hex, y_hex+height]
        bottom_point = [x_hex, y_hex+y_dist]
        line = geojson.LineString([top_point, bottom_point])
        groyne = geojson.Feature(id="groyne" + str(feature.id).zfill(2), geometry=line)
        groyne.properties["active"] = True
        structures.append(groyne)
    structures = geojson.FeatureCollection(structures)
    with open('structures_test.geojson', 'w') as f:
        geojson.dump(structures, f, sort_keys=True, indent=2)
    return structures


def create_LTDs(hexagons):
    """
    Results are better with 59 degrees for some reason that I cannot figure
    out yet.
    """
    sin = np.sin(np.deg2rad(60))
    cosin = np.cos(np.deg2rad(60))
    height = 0.0
    x_dist = 0.0
    y_dist = 0.0
    ltd_features = []
    for feature in hexagons.features:
        """
        Ideally would also want to do this with a try/except KeyError, but -1
        index would find a hexagon.
        """
        edge = False
        west_edge = False
        east_edge = False
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0 or feature.id == 1:
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
        ltd = geojson.Feature(id="LTD" + str(feature.id).zfill(2), geometry=line)
        ltd.properties["active"] = False
        ltd_features.append(ltd)
    ltd_features = geojson.FeatureCollection(ltd_features)
    with open('ltds_test_line_correct.geojson', 'w') as f:
        geojson.dump(ltd_features, f, sort_keys=True, indent=2)
    return ltd_features


def create_LTDs_old(hexagons, north_side=True):
    """
    Results are better with 59 degrees for some reason that I cannot figure
    out yet.
    """
    sin = np.sin(np.deg2rad(60))
    cosin = np.cos(np.deg2rad(60))
    height = 0.0
    size = 0.0
    x_dist = 0.0
    y_dist = 0.0
    x_jump = 0.0
    y_jump = 0.0
    ltd_features = []
    for feature in hexagons.features:
        """
        Ideally would also want to do this with a try/except KeyError, but -1
        index would find a hexagon.
        """
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
            size = ((1 / 10) * height)
            x_dist = sin * height
            y_dist = cosin * height
            x_jump = sin * cosin * size
            y_jump = sin * sin * size
            edge = True
            west_edge = True
        else:
            left_hex = hexagons[feature.id - 1]
            shape = geometry.asShape(left_hex.geometry)
            y_hex_left = shape.centroid.y
        try:
            right_hex = hexagons[feature.id + 1]
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
        mid_point_top = [x_hex, y_hex+size]
        mid_point_bottom = [x_hex, y_hex-size]
        if hex_left_north and hex_right_north:
            # LTD shape: high to high: \_/
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point_top = [x_top_left+x_jump, y_top_left+y_jump]
            left_point_bottom = [x_top_left-x_jump, y_top_left-y_jump]
            x_top_left = x_hex + x_dist
            right_point_top = [x_top_left-x_jump, y_top_left+y_jump]
            right_point_bottom = [x_top_left+x_jump, y_top_left-y_jump]
        elif hex_left_north and not hex_right_north:
            # LTD shape high to low: `-_
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point_top = [x_top_left+x_jump, y_top_left+y_jump]
            left_point_bottom = [x_top_left-x_jump, y_top_left-y_jump]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex - y_dist
            right_point_top = [x_top_left+x_jump, y_top_left+y_jump]
            right_point_bottom = [x_top_left-x_jump, y_top_left-y_jump]
        elif not hex_left_north and hex_right_north:
            # LTD shape low to high: _-`
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point_top = [x_top_left-x_jump, y_top_left+y_jump]
            left_point_bottom = [x_top_left+x_jump, y_top_left-y_jump]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex + y_dist
            right_point_top = [x_top_left-x_jump, y_top_left+y_jump]
            right_point_bottom = [x_top_left+x_jump, y_top_left-y_jump]
        else:
            # LTD shape low to high: /`\
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point_top = [x_top_left-x_jump, y_top_left+y_jump]
            left_point_bottom = [x_top_left+x_jump, y_top_left-y_jump]
            x_top_left = x_hex + x_dist
            right_point_top = [x_top_left+x_jump, y_top_left+y_jump]
            right_point_bottom = [x_top_left-x_jump, y_top_left-y_jump]
        polygon = geojson.Polygon([[left_point_top, mid_point_top,
                                    right_point_top, right_point_bottom,
                                    mid_point_bottom, left_point_bottom,
                                    left_point_top]])
        ltd = geojson.Feature(id=feature.id, geometry=polygon)
        ltd.properties["active"] = False
        ltd_features.append(ltd)
    ltd_features = geojson.FeatureCollection(ltd_features)
    if north_side:
        with open('ltds_test_north.geojson', 'w') as f:
            geojson.dump(ltd_features, f, sort_keys=True, indent=2)
    else:
        with open('ltds_test_south.geojson', 'w') as f:
            geojson.dump(ltd_features, f, sort_keys=True, indent=2)
    return ltd_features


if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    hexagons = determine_dikes(hexagons)
    hexagons = determine_channel(hexagons)
    with open('hexagons_with_structures.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    channel = get_channel(hexagons)
    #groynes = create_groynes(channel)
    #ltds = create_LTDs(channel)
    structures = create_structures(channel)
    D3D.geojson2pli(structures, name="structures_test")
