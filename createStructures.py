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
    """
    Function that determines the dike locations (z value above dike level
    threshold). Sets the feature properties accordingly.
    """
    for feature in hexagons.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
        if feature.properties["z_reference"] >= 4:
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


def determine_floodplains_and_behind_dikes(hexagons):
    north_channel = []
    south_channel = []
    dikes_north = []
    dikes_south = []
    for feature in hexagons.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
        if feature.properties["north_side_channel"]:
            north_channel.append(feature)
        elif feature.properties["south_side_channel"]:
            south_channel.append(feature)
        elif feature.properties["north_dike"] is True:
            dikes_north.append(feature)
        elif feature.properties["south_dike"] is True:
            dikes_south.append(feature)
    north_channel = geojson.FeatureCollection(north_channel)
    south_channel = geojson.FeatureCollection(south_channel)
    dikes_north = geojson.FeatureCollection(dikes_north)
    dikes_south = geojson.FeatureCollection(dikes_south)
    for feature in hexagons.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
        try:
            channel_north = north_channel[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a main channel in the north")
            continue
        try:
            channel_south = south_channel[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a main channel in the south")
            continue
        try:
            dike_top = dikes_north[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a complete dike in the north")
            continue
        try:
            dike_bottom = dikes_south[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a complete dike in the south")
            continue
        if feature.id < dike_top.id:
            feature.properties["behind_dike"] = True
            feature.properties["dike_reference"] = dike_top.id
        elif feature.id > dike_bottom.id:
            feature.properties["behind_dike"] = True
            feature.properties["dike_reference"] = dike_bottom.id
        else:
            feature.properties["behind_dike"] = False
            feature.properties["dike_reference"] = None
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["floodplain_north"] = False
            feature.properties["floodplain_south"] = False
        else:
            if (feature.id < channel_north.id and
                feature.id > dike_top.id):
                feature.properties["floodplain_north"] = True
                feature.properties["floodplain_south"] = False
            elif (feature.id > channel_south.id and
                  feature.id < dike_bottom.id):
                feature.properties["floodplain_north"] = False
                feature.properties["floodplain_south"] = True
            else:
                feature.properties["floodplain_north"] = False
                feature.properties["floodplain_south"] = False
    return hexagons


def determine_channel(hexagons):
    """
    Function that determines the main channel location (z value below main
    channel threshold). Sets the feature properties accordingly.
    """
    for feature in hexagons.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
        if feature.properties["z_reference"] < 1:
            next_hexagon = hexagons[feature.id + 1]
            if next_hexagon.properties["z_reference"] == 0:
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
    """
    Function that only returns the main channel hexagons.
    """
    hexagons_copy = deepcopy(hexagons)
    channel = []
    for feature in hexagons_copy.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
        if feature.properties["main_channel"]:
            channel.append(feature)
    channel = geojson.FeatureCollection(channel)
    for i, feature in enumerate(channel.features):
        feature.id = i
    return channel


def create_structures(hexagons):
    """
    Function that determines where the structures (groynes and ltds) should be
    located in the main channel at the start of the game. Creates linestrings
    for both and returns them as a single featurecollection.
    
    NOTE: Results are better with 59 degrees for some reason that I cannot
    figure out yet.
    """
    sin = np.sin(np.deg2rad(60))
    cosin = np.cos(np.deg2rad(60))
    height = 0.0
    x_dist = 0.0
    y_dist = 0.0
    groyne_dist = 0.0
    structures = []
    for feature in hexagons.features:
        #if feature.properties["ghost_hexagon"]:
        #    continue
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
        """
        # The combination of groynes and ltds makes the model extremely slow,
        # especially at crest height 0 for the ltds. With a crest height of 3,
        # same as the groynes, the model runs smoother, albeit still ~5 slower.
        # ltds are therefore currently placed in this comment block.
        # 
        # TODO: figure out a fix to make the model be able to smoothly
        # transition from groynes to ltds.
        
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
        ltd.properties["crest_level"] = 0.00000001
        structures.append(ltd)
        """

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
    if False:
        # saving is currently skipped, hence in if False statement.
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
