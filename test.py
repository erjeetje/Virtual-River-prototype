# -*- coding: utf-8 -*-
"""
Created on Sat Jun 29 21:31:35 2019

@author: HaanRJ
"""

import os
import time
import geojson
import numpy as np
import gridMapping as gridmap
import modelInterface as D3D
from shapely import geometry
from scipy.spatial import cKDTree


def kdtree(grid):
    grid_coor = []
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        x = point.centroid.x
        y = point.centroid.y
        grid_coor.append([x, y])
    grid_coor = np.array(grid_coor)
    grid_tree = cKDTree(grid_coor)
    return grid_tree


def index_hexagons(hexagons, grid_tree):
    for feature in hexagons.features:
        midpoint = geometry.asShape(feature.geometry)
        x = midpoint.centroid.x
        y = midpoint.centroid.y
        xy = np.array([x, y])
        dist, index = grid_tree.query(xy)
        feature.properties["face_cell"] = index
        print(feature.properties["face_cell"])  
    return hexagons


def update_waterlevel(model, hexagons):
    t0 = time.time()
    s1 = model.get_var('s1')
    for feature in hexagons.features:
        index = feature.properties["face_cell"]
        feature.properties["water_level"] = s1[index]
        print(feature.properties["water_level"])
    t1 = time.time()
    print(t1-t0)
    return hexagons


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    model = D3D.initialize_model()
    face_grid = gridmap.read_face_grid(model)
    grid_tree = kdtree(face_grid)
    for i in range(7):
        hexagons = gridmap.read_hexagons(
                filename='hexagons%d.geojson' % i, path=test_path)
        hexagons = index_hexagons(hexagons, grid_tree)
        with open(os.path.join(dir_path, 'hexagons%d.geojson' % i), 'w') as f:
            geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return
    
    
if __name__ == "__main__":
    main()