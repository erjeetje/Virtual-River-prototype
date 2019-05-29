# -*- coding: utf-8 -*-
"""
Created on Tue May 21 14:23:49 2019

@author: HaanRJ
"""

import geojson
import numpy as np
import gridMapping as gridmap


def hex_to_points(model, hexagons, grid, test=True):
    frcu = model.get_var('frcu')
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        location = feature.properties["location"]
        hexagon = hexagons_by_id[location]
        if test:
            if hexagon.properties['z'] == 0:
                landuse = 9
            elif hexagon.properties['z'] >= 4:
                landuse = 10
            else:
                landuse = 2
        else:
            feature.properties["landuse"] = hexagon.properties["landuse"] 
        friction = landuse_to_friction(feature.properties['landuse'])
        frcu[feature.id] = friction
    return grid


def landuse_to_friction(landuse):
    # landuse range between 0 and 9, with a subdivision for 0:
    # 0: built environment
    # 1: agriculture; production meadow/crop field
    # 2: natural grassland
    # 3: reed; 'ruigte'
    # 4: shrubs; hard-/softwood
    # 5: forest; hard-/softwood
    # 6: mixtype class; mix between grass/reed/shrubs/forest
    # 7: water body; sidechannel (connected to main channel) or lake
    # 8: main channel; river bed with longitudinal training dams
    # 9: main channel; river bed with groynes
    # 10: dike
    if landuse == 9:
        friction = 1000
    else:
        friction = 1
    return friction


if __name__ == '__main__':
    hexagons = gridmap.read_hexagons(filename='temp')
    grid = gridmap.read_grid()
    grid = gridmap.hex_to_points(hexagons, grid, start=True, turn=0)
    grid = hex_to_points(hexagons, grid)
    gridmap.run_model(grid)
