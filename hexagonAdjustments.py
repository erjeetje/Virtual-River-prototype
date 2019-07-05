# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 13:45:47 2019

@author: HaanRJ
"""

import os
import geojson
import gridMapping as gridmap
from shapely import geometry


def add_bedslope(hexagons, slope):
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        x_hex = abs(x_hex - 600)
        feature.properties["bedslope_correction"] = slope * x_hex
    return hexagons


def z_correction(hexagons, initialized=True):
    for feature in hexagons.features:
        if (feature.properties["ghost_hexagon"] and initialized):
            continue
        else:
            feature.properties["z"] = (feature.properties["z"] +
                              feature.properties["bedslope_correction"])
    return hexagons


def change_bedslope(hexagons, slope):
    for feature in hexagons.features:
        feature.properties["z"] = (feature.properties["z_reference"] +
                          feature.properties["bedslope_correction"])
    return hexagons


def change_zref(hexagons):
    for feature in hexagons.features:
        feature.properties["z"] = feature.properties["z_reference"] * 1.2
    return hexagons


def update_hex(hexagons1, hexagons2):
    for feature in hexagons1.features:
        if feature.properties["ghost_hexagon"]:
            continue
        else:
            reference_hex = hexagons2[feature.id]
            feature.properties["z_reference"] = reference_hex.properties["z"]
    return hexagons1


def fix(turn):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files_copy')
    save_path = os.path.join(dir_path, 'test_files')
    hexagons1 = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=save_path)
    hexagons2 = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    hexagons1 = update_hex(hexagons1, hexagons2)
    #slope = 10**-3
    #hexagons = add_bedslope(hexagons, slope)
    #for feature in hexagons.features:
    #    feature.properties["z_reference"] = feature.properties["z"]
    #hexagons = z_correction(hexagons)
    hexagons1 = change_zref(hexagons1)
    """
    for feature in hexagons.features:
        if feature.properties["z"] < 1:
            feature.properties["main_channel"] = True
    """
    with open(os.path.join(save_path, 'hexagons%d.geojson' % turn),
              'w') as f:
        geojson.dump(hexagons1, f, sort_keys=True, indent=2)
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
    for i in range(0, 8):
        fix(turn)
        turn +=1
    
if __name__ == '__main__':
    main()