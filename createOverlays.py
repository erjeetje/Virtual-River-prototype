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
    #determine_ownership3()
    hexagons = random_points(hexagons)
