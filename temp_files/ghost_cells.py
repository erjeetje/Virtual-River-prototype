# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 12:15:27 2019

@author: HaanRJ
"""

import os
import geojson
import numpy as np
import gridMapping as gridmap
from shapely import geometry


def create_features(height, width):
    """
    Function that calculates the midpoint coordinates of each hexagon in the
    transformed picture.
    """
    # determine size of grid circles from image and step size in x direction
    radius = (height / 10)
    x_step = np.cos(np.deg2rad(30)) * radius
    origins = []
    column = []
    # determine x and y coordinates of gridcells midpoints
    for a in range(1, 16):  # range reflects gridsize in x direction
        x = (x_step * a)
        for b in range(1, 11):  # range reflects gridsize in y direction
            if a % 2 == 0:
                if b == 10:
                    continue
                y = (radius * b)
            else:
                y = (radius * (b - 0.5))
            origins.append([x, y])
            column.append(a)
    origins = np.array(origins)
    board_cells = len(origins)
    """
    code to add ghost cells.
    """
    y_jump = radius/2
    dist = y_jump/np.cos(np.deg2rad(30))
    x_jump = dist/2
    features = []
    for i, (x, y) in enumerate(origins):
        # determine all the corner points of the hexagon
        point1 = [x+dist, y]
        point2 = [x+x_jump, y+y_jump]
        point3 = [x-x_jump, y+y_jump]
        point4 = [x-dist, y]
        point5 = [x-x_jump, y-y_jump]
        point6 = [x+x_jump, y-y_jump]
        # create a geojson polygon for the hexagon
        polygon = geojson.Polygon([[point1, point2, point3, point4, point5,
                                    point6, point1]])
        feature = geojson.Feature(id=i, geometry=polygon)
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
        feature.properties["column"] = column[i]
        feature.properties["tygron_id"] = i
        # these x and y centers are not actually relevant --> features are
        # transformed to other coordinates.
        feature.properties["x_center"] = int(round(x))
        feature.properties["y_center"] = int(round(y))
        feature.properties["ghost_cell"] = False
        features.append(feature)
    x_left = origins[0][0] - x_step
    x_right = origins[-1][0] + x_step
    ghost_origins = []
    for b in range(1,10):
        x = x_left
        y = radius * b
        ghost_origins.append([x, y])
    for b in range(1,10):
        x = x_right
        y = radius * b
        ghost_origins.append([x, y])
    vert_middle = width / 2
    min_column = min(column)
    max_column = max(column)
    for i, (x, y) in enumerate(ghost_origins):
        # determine all the corner points of the hexagon
        point1 = [x+dist, y]
        point2 = [x+x_jump, y+y_jump]
        point3 = [x-x_jump, y+y_jump]
        point4 = [x-dist, y]
        point5 = [x-x_jump, y-y_jump]
        point6 = [x+x_jump, y-y_jump]
        # create a geojson polygon for the hexagon
        polygon = geojson.Polygon([[point1, point2, point3, point4, point5,
                                    point6, point1]])
        ghost_id = i + board_cells
        feature = geojson.Feature(id=ghost_id, geometry=polygon)
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
        if x < vert_middle:
            feature.properties["column"] = min_column - 1
        else:
            feature.properties["column"] = max_column + 1
        feature.properties["tygron_id"] = None
        # these x and y centers are not actually relevant --> features are
        # transformed to other coordinates.
        feature.properties["x_center"] = int(round(x))
        feature.properties["y_center"] = int(round(y))
        feature.properties["ghost_cell"] = True
        features.append(feature)
    # create geojson featurecollection with all hexagons.
    features = geojson.FeatureCollection(features)
    with open('ghost_cells_test.geojson', 'w') as f:
        geojson.dump(features, f, sort_keys=True, indent=2)
    return features


def create_ghost_cells(hexagons):
    columns = []
    hex_coor = []
    geometries = []
    for feature in hexagons.features:
        column = feature.properties["column"]
        if column not in columns:
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            y_hex = shape.centroid.y
            geometries.append(feature.geometry)
            hex_coor.append([x_hex, y_hex])
            columns.append(column)
    hex_column1 = hex_coor[0]
    hex_column2 = hex_coor[1]
    hex_column3 = hex_coor[-2]
    hex_column4 = hex_coor[-1]
    #print(geometries)
    #print(columns[0], columns[1], columns[-2], columns[-1])
    #print(hex_column1, hex_column2, hex_column3, hex_column4)
    #ghost_cell


def main():
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    turn = 0
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    """
    height = 1000
    ratio = 1.3861874976470018770202169598726
    width = int(round(height * ratio))
    hexagons = create_features(height, width)
    #create_ghost_cells(hexagons)
    
    
if __name__ == "__main__":
    main()