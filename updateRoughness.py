# -*- coding: utf-8 -*-
"""
Created on Tue May 21 14:23:49 2019

@author: HaanRJ
"""

import geojson
import numpy as np
import gridMapping as gridmap


def hex_to_points(hexagons, grid):
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        try:
            location = feature.properties["nearest"][0]
        except IndexError:
            location = feature.properties["nearest"]
        hexagon = hexagons_by_id[location]
        land_type = hexagon.properties["landuse"]
        feature.properties["landuse"] = land_type
        
    return grid


if __name__ == '__main__':
    hexagons = gridmap.read_hexagons(filename='temp')
    grid = gridmap.read_grid()
    grid = gridmap.hex_to_points(hexagons, grid, start=True, turn=0)
    grid = hex_to_points(hexagons, grid)
    gridmap.run_model(grid)
