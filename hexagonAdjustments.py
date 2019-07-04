# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 13:45:47 2019

@author: HaanRJ
"""

import os
import geojson
import gridMapping as gridmap
from shapely import geometry


def z_correction(hexagons, slope):
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        x_hex = abs(x_hex - 600)
        feature.properties["z"] = feature.properties["z"] + (slope * x_hex)
        #print("Hexagon at x is " + str(x_hex) + " has corrected height " +
        #      str(feature.properties["z"]))
    return hexagons

def fix(turn):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    for feature in hexagons.features:
        if feature.properties["z"] < 1:
            feature.properties["main_channel"] = True
    with open(os.path.join(test_path, 'hexagons%d.geojson' % turn),
              'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return


def main():
    """
    turn = 0
    slope = 10**-4
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    hexagons = z_correction(hexagons, slope)
    """
    turn = 0
    for i in range(0, 9):
        fix(turn)
        turn +=1
    
if __name__ == '__main__':
    main()