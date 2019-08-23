# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 14:06:48 2019

@author: HaanRJ
"""

import geojson
import numpy as np
from shapely import geometry
from copy import deepcopy
from scipy.spatial import cKDTree
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
    
    Also sorts the channel from west to east, including the ghost hexagons.
    """
    hexagons_copy = deepcopy(hexagons)
    channel = []
    for feature in hexagons_copy.features:
        if (not feature.properties["ghost_hexagon"] or
            feature.id > 180):
            continue
        if feature.properties["main_channel"]:
            channel.append(feature)
    for feature in hexagons_copy.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["main_channel"]:
            channel.append(feature)
    for feature in hexagons_copy.features:
        if (not feature.properties["ghost_hexagon"] or
            feature.id <= 180):
            continue
        if feature.properties["main_channel"]:
            channel.append(feature)
    channel = geojson.FeatureCollection(channel)
    for i, feature in enumerate(channel.features):
        feature.properties["reference_id"] = feature.id
        feature.id = i
    with open('channel.geojson', 'w') as f:
        geojson.dump(channel, f, sort_keys=True, indent=2)
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
        #groyne = geojson.Feature(id="groyne" + str(feature.id).zfill(2), geometry=line)
        groyne = geojson.Feature(id=feature.id, geometry=line)
        groyne.properties["active"] = True
        groyne.properties["reference_id"] = feature.properties["reference_id"]
        groynes.append(groyne)
    groynes = geojson.FeatureCollection(groynes)
    with open('groynes_test_line.geojson', 'w') as f:
        geojson.dump(groynes, f, sort_keys=True, indent=2)
    return groynes


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
            x_dist = sin * height * 0.95
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
        if west_edge:
            line = geojson.LineString([mid_point, right_point])
        elif east_edge:
            line = geojson.LineString([left_point, mid_point])
        else:
            line = geojson.LineString([left_point, mid_point, right_point])
        #ltd = geojson.Feature(id="LTD" + str(feature.id).zfill(2), geometry=line)
        ltd = geojson.Feature(id=feature.id, geometry=line)
        ltd.properties["active"] = False
        ltd.properties["reference_id"] = feature.properties["reference_id"]
        ltd_features.append(ltd)
    ltd_features = geojson.FeatureCollection(ltd_features)
    with open('ltds_test_line_correct.geojson', 'w') as f:
        geojson.dump(ltd_features, f, sort_keys=True, indent=2)
    return ltd_features


def index_structures(structures, grid, mode="groyne"):
    structures_coor = []
    structures_id = []
    # get x, y coordinates of each point and add it to hex_coor list to create
    # a cKDTree. Also add the shape of the hexagon to polygons to create a
    # single polygon of the game board.
    for feature in structures.features:
        pts = feature.geometry["coordinates"]
        for point in pts:
            structures_coor.append(point)
            structures_id.append(feature.id)
    structures_coor = np.array(structures_coor)
    length = len(structures_coor)
    structures_locations = cKDTree(structures_coor)
    z_correct = "z_" + mode
    for feature in grid.features:
        xy = feature.geometry["coordinates"]
        dist, index = structures_locations.query(xy, distance_upper_bound = 25)
        if index < length:
            feature.properties[mode] = structures_id[index]
            structure = structures.features[structures_id[index]]
            shape = geometry.asShape(structure.geometry)
            point = geometry.asShape(feature.geometry)
            distance = point.distance(shape)
            try:
                covered = feature.properties[z_correct]
                print(covered)
            except KeyError:
                covered = 0
            if distance < 2.5:
                feature.properties[z_correct] = max(covered, 6)
            elif distance < 5:
                feature.properties[z_correct] = max(covered, 4)
            elif distance < 7.5:
                feature.properties[z_correct] = max(covered, 2)
            else:
                feature.properties[z_correct] = max(covered, 0)
            if covered != 0:
                print("found value: " + str(covered) + ". set value: " +
                      str(feature.properties[z_correct]))
        else:
            try:
                covered = feature.properties[z_correct]
            except KeyError:
                feature.properties[mode] = None
                pass
    return grid


def apply_hydraulic_structures_corrections(grid):
    for feature in grid.features:
        if feature.properties["groyne_active"]:
            if feature.properties["groyne"] != None:
                height_correction = (feature.properties["z_groyne"] +
                                     feature.properties["bedslope_correction"])
                if height_correction < feature.properties["z"]:
                    continue
                else:
                    feature.properties["z"] = height_correction
        if feature.properties["ltd_active"]:
            if feature.properties["ltd"] != None:
                height_correction = (feature.properties["z_ltd"] +
                                     feature.properties["bedslope_correction"])
                if height_correction < feature.properties["z"]:
                    continue
                else:
                    feature.properties["z"] = height_correction
    with open('node_grid_with_groynes3.geojson', 'w') as f:
        geojson.dump(grid, f, sort_keys=True, indent=2)
    return


def create_buildings(hexagons, grid):
    building_size = 20
    building_ids = []
    buildings = []
    for feature in hexagons.features:
        if feature.properties["behind_dike"]:
            continue
        if (feature.properties["z_reference"] < 4 and
            feature.properties["landuse"] == 0):
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            y_hex = shape.centroid.y
            point1 = [x_hex - building_size, y_hex + building_size]
            point2 = [x_hex + building_size, y_hex + building_size]
            point3 = [x_hex + building_size, y_hex - building_size]
            point4 = [x_hex - building_size, y_hex - building_size]
            polygon = geojson.Polygon([[point1, point2, point3, point4,
                                        point1]])
            building = geojson.Feature(id=feature.id, geometry=polygon)
            building_ids.append(feature.id)
            buildings.append(building)
    buildings = geojson.FeatureCollection(buildings)
    for feature in grid.features:
        if type(feature.properties["nearest"]) is int:
            if feature.properties["nearest"] not in building_ids:
                continue
            else:
                reference = building_ids.index(feature.properties["nearest"])
        else:
            continue
        """
        elif any(True for x in feature.properties["nearest"]
                 if x not in building_ids):
            continue
        else:
            reference = building_ids.index(feature.properties["nearest"][0])
        """
        point = geometry.asShape(feature.geometry)
        building = buildings.features[reference]
        polygon = geometry.asShape(feature.geometry)
        if polygon.contains(point):
            feature.properties["building_active"] = True
            feature.properties["z_building"] = 4
    return grid


def add_buildings(grid):
    for feature in grid.features:
        if not feature.properties["building_active"]:
            continue
        else:
            feature.properties["z"] += (
                    feature.properties["z_building"] -
                    feature.properties["bedslope_correction"])
    with open('node_grid_with_buildings.geojson', 'w') as f:
        geojson.dump(grid, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    with open('storing_files\\filled_node_grid0.geojson', 'r') as f:
        filled_node_grid = geojson.load(f)
    #hexagons = determine_dikes(hexagons)
    #hexagons = determine_channel(hexagons)
    #with open('hexagons_with_structures.geojson', 'w') as f:
    #    geojson.dump(hexagons, f, sort_keys=True, indent=2)
    #channel = get_channel(hexagons)
    #structures = create_structures(channel)
    #D3D.geojson2pli(structures, name="structures_test")
    """
    channel = get_channel(hexagons)
    groynes = create_groynes(channel)
    ltds = create_LTDs(channel)
    filled_node_grid = index_structures(groynes, filled_node_grid)
    filled_node_grid = index_structures(ltds, filled_node_grid, mode="ltd")
    filled_node_grid = add_bedslope(filled_node_grid)
    filled_node_grid = set_active(filled_node_grid)
    apply_hydraulic_structures_corrections(filled_node_grid)
    """
    filled_node_grid = create_buildings(hexagons, filled_node_grid)
    add_buildings(filled_node_grid)
