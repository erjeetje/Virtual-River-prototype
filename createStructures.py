# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 14:06:48 2019

@author: HaanRJ
"""

import geojson
from shapely import geometry


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


if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    hexagons = determine_dikes(hexagons)
    hexagons = determine_channel(hexagons)
    with open('hexagons_with_structures.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
