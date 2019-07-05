# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 13:45:47 2019

@author: HaanRJ
"""


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


def main():
    return
    
if __name__ == '__main__':
    main()