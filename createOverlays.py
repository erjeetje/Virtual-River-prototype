# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 06:37:58 2019

@author: HaanRJ
"""

import random
import geojson
import numpy as np
from scipy.spatial import cKDTree
from shapely import geometry
from shapely.ops import unary_union
import gridMapping as gridmap


"""
To do:
    - get the number of floodplain hexagon cells
    - declare owners (water, nature, <third>)
    - establish number of hexagons per player
    - generate patches of size 3 to 5
    - update hexagon properties
"""


def determine_neighbours(hexagons):
    hex_coor = []
    polygons = []
    hexagon0_y = 0
    hexagon1_y = 0
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            hexagon0_y = y_hex
        if feature.id == 1:
            hexagon1_y = y_hex
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    limit = abs((hexagon0_y - hexagon1_y) * 1.5)
    total_hex = len(hexagons.features)
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        # find all hexagons within the limit radius
        dist, indices = hex_locations.query(
                xy, k=7, distance_upper_bound=limit)
        # remove missing neighbours (return as self.n, equal to total_hex)
        indices = remove_values_from_array(indices, total_hex)
        # convert from int32 to regular int (otherwise JSON error)
        indices = list(map(int, indices))
        # remove itself
        indices.pop(0)
        print("Neighbouring hexagons for hexagon " + str(feature.id) +
              " are: " + str(indices))
        feature.properties["neighbours"] = indices
    return hexagons


def remove_values_from_array(array, val):
   return [value for value in array if value != val]


def determine_floodplains(hexagons):
    north_channel = []
    south_channel = []
    dikes_north = []
    dikes_south = []
    for feature in hexagons.features:
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


def determine_floodplains2(hexagons):
    north_channel = []
    south_channel = []
    dikes_north = []
    dikes_south = []
    for feature in hexagons.features:
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
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["floodplain_north"] = False
            feature.properties["floodplain_south"] = False
        else:
            try:
                channel_north = north_channel[feature.properties["column"]-1]
            except KeyError:
                print("area does not have a complete dike in the north")
                continue
            try:
                channel_south = south_channel[feature.properties["column"]-1]
            except KeyError:
                print("area does not have a complete dike in the south")
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
            #feature.properties["floodplain_north"] = True
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


def owners(hexagons):
    count = 0
    for feature in hexagons.features:
        if feature.properties["floodplain"]:
            count += 1
    print("number of floodplain cells: ")
    return hexagons


def determine_ownership(hexagons):
    owner = ["red", "green" ,"blue"]
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            continue
        count += 1
    ownership = random.choices(owner, k=count)
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["owner"] = None
        else:
            feature.properties["owner"] = ownership[count]
            count += 1
    with open('ownership_test.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return hexagons



def determine_ownership4(hexagons):
    owner = ["red", "green" ,"blue"]
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            continue
        count += 1
    ownership = random.choices(owner, k=count)
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["owner"] = None
        else:
            feature.properties["owner"] = ownership[count]
            count += 1
    with open('ownership_test.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return hexagons


def determine_ownership2(hexagons):
    hex_coor = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    count = 0
    owner = random.randint(1, 3)
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        dist, index = hex_locations.query(xy, k=7)
    return hexagons


def determine_ownership3():
    ownership = []
    ownership = add_ownership(ownership)
    while len(ownership) < 100:
        ownership = add_ownership(ownership)
    print(ownership)
    return


def add_ownership(ownership):
    length = random.randint(3, 5)
    owner = random.randint(1, 3)
    print(length)
    for i in range(0, length):
        print(owner)
        ownership.append(owner)
    return ownership
"""
Separate north and south floodplains ? ==>
Create empty list of ownership ==>
Create random len(3-5) list of 

Generate (semi) random points within the board ==> cKDTree ==> index hexagons
to random points ==> assign ownership
"""

def random_points(hexagons):
    polygons = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        polygons.append(shape)
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    line = list(geojson.utils.coords(board_feature))

    # determine the bounding box coordinates of the board.
    minx = 0.0
    miny = 0.0
    maxx = 0.0
    maxy = 0.0
    for x, y in line:
        if x < minx:
            minx = x
        elif x > maxx:
            maxx = x
        if y < miny:
            miny = y
        elif y > maxy:
            maxy = y
    x_clusters = 6
    y_clusters = 4
    x_step = (abs(minx) + maxx) / x_clusters
    y_step = (abs(miny) + maxy) / y_clusters
    random_points = []
    ownership_points = []
    seed_length = x_clusters * y_clusters
    owner = ["red", "green" ,"blue"]
    ownership = random.choices(owner, k=seed_length)
    i = 0
    for a in range(0, x_clusters):  # range reflects gridsize in x direction
        for b in range(0, y_clusters):  # range reflects gridsize in y direction
            x = (x_step * random.random()) + (x_step * a) - abs(minx)
            y = (y_step * random.random()) + (y_step * b) - abs(miny)
            xy = [round(x), round(y)]
            random_points.append(xy)
            point = geojson.Point(xy)
            feature = geojson.Feature(id=i, geometry=point)
            feature.properties["owner"] = ownership[i]
            ownership_points.append(feature)
            i += 1
    random_points = np.array(random_points)
    points_locations = cKDTree(random_points)
    ownership_points = geojson.FeatureCollection(ownership_points)
    #points_by_id = {feature.id: feature for feature in ownership_points.features}
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        dist, index = points_locations.query(xy)
        feature.properties["ownership_index"] = index
        point = ownership_points[index]
        feature.properties["owner"] = point.properties["owner"]
        print("ownership for hexagon " + str(feature.id) + ": " +
              str(feature.properties["owner"]))
    return hexagons


if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    """
    hexagons = gridmap.hexagons_to_fill(hexagons)
    hexagons = determine_ownership(hexagons)
    """
    hexagons = determine_neighbours(hexagons)
    hexagons = determine_floodplains(hexagons)
    #hexagons = random_points(hexagons)
    with open('floodplain_test.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)