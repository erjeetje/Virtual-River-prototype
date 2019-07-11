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


def test_mode_z_correction(hexagons):
    for feature in hexagons.features:
        feature.properties["z"] = ((feature.properties["z_reference"] * 1.2) +
                          feature.properties["bedslope_correction"])
    return hexagons


def add_mixtype_ratio(hexagons, ratio):
    for feature in hexagons.features:
        feature.properties["mixtype_ratio"] = ratio
    return hexagons


def find_factory(hexagons):
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        feature.properties["factory"] = False
        if not (feature.properties["floodplain_north"] or
                feature.properties["floodplain_south"]):
            continue
        else:
            if feature.properties["landuse"] == 0:
                print("Hexagon " + str(feature.id) + " has landuse 0.")
                farm = False
                neighbours = feature.properties["neighbours"]
                for i in range(0, len(neighbours)):
                    reference_hex = hexagons[neighbours[i]]
                    if reference_hex.properties["landuse"] == 1:
                        farm = True
                if not farm:
                    feature.properties["factory"] = True
                    print("Hexagon " + str(feature.id) + " is a factory.")
    return hexagons


def biosafe_area(hexagons):
    for feature in hexagons.features:
        if (feature.properties["ghost_hexagon"] or
            feature.properties["behind_dike"] or 
            feature.properties["south_dike"] or
            feature.properties["north_dike"]):
            feature.properties["biosafe"] = False
        else:
            feature.properties["biosafe"] = True
    return hexagons


def main():
    turn=0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    hexagons = biosafe_area(hexagons)
    with open('hexagons_biosafe.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return
    
if __name__ == '__main__':
    main()