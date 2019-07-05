# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 09:24:42 2019

@author: HaanRJ
"""

import os
import geojson
import numpy as np
import matplotlib.pyplot as plt
import gridMapping as gridmap
import modelInterface as D3D
from shapely import geometry


def water_levels(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    water_level_columns = [[] for i in range(15)]
    x_values = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["behind_dike"] or
            feature.properties["north_dike"] or
            feature.properties["south_dike"]):
            continue
        else:
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            x_values.append(x_hex)
            water_level = feature.properties["water_level"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(water_level)
    x_output = []
    for x in x_values:
        x = round(x, 2)
        if x not in x_output:
            x_output.append(x)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    return water_level, x_output


def water_levels2(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'storing_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    water_level_columns = [[] for i in range(15)]
    x_values = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["main_channel"]:
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            x_values.append(x_hex)
            water_level = feature.properties["water_level"]  # - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(water_level)
    x_output = []
    for x in x_values:
        x = round(x, 2)
        if x not in x_output:
            x_output.append(x)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    return water_level, x_output


def plot_water_levels(xvals, yvals, turn=0, fig=None, ax=None):
    xvals = []
    for i in range(len(yvals)):
        xvals.append(i * 250)
    if fig is None:
        fig, ax = plt.subplots(1)
        ax.set_xlabel('river section (meters)')
        ax.set_ylabel('water levels (meters)')
        ax.set_ylim([3.5, 5.5])
    if turn == 1:
        label = "initial board"
    elif turn == 10:
        label = 'dike level'
    else:
        label = ("board after turn " + str(turn-1))
    ax.plot(xvals, yvals, label=label)
    ax.legend(loc='upper right')
    plt.show
    return fig, ax


def dike_levels(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'storing_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    water_level_columns = [[] for i in range(15)]
    x_values = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"]):
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            x_values.append(x_hex)
            dike_level = feature.properties["z"] - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(dike_level)
    x_output = []
    for x in x_values:
        x = round(x, 2)
        if x not in x_output:
            x_output.append(x)
    dike_level = []
    print(water_level_columns)
    for values in water_level_columns:
        dike_height = min(values)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        dike_level.append(dike_height)
    return dike_level, x_output


def main():
    """
    model = D3D.initialize_model()
    face_grid = gridmap.read_face_grid(model)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'face_grid.geojson'), 'w') as f:
        geojson.dump(face_grid, f, sort_keys=True, indent=2)
    """
    
    #water_level0, x0 = water_levels2(turn=0)
    water_level1, x1 = water_levels2(turn=1)
    water_level2, x2 = water_levels2(turn=2)
    water_level3, x3 = water_levels2(turn=3)
    water_level4, x4 = water_levels2(turn=4)
    water_level5, x5 = water_levels2(turn=5)
    water_level6, x6 = water_levels2(turn=6)
    water_level7, x7 = water_levels2(turn=7)
    #water_level8, x8 = water_levels2(turn=8)
    #fig, ax = plot_water_levels(x0, water_level0, turn=0)
    fig, ax = plot_water_levels(x1, water_level1, turn=1)
    fig, ax = plot_water_levels(x2, water_level2, turn=2, fig=fig, ax=ax)
    fig, ax = plot_water_levels(x3, water_level3, turn=3, fig=fig, ax=ax)
    fig, ax = plot_water_levels(x4, water_level4, turn=4, fig=fig, ax=ax)
    fig, ax = plot_water_levels(x5, water_level5, turn=5, fig=fig, ax=ax)
    fig, ax = plot_water_levels(x6, water_level6, turn=6, fig=fig, ax=ax)
    fig, ax = plot_water_levels(x7, water_level7, turn=7, fig=fig, ax=ax)
    #fig, ax = plot_water_levels(x8, water_level8, turn=8, fig=fig, ax=ax)
    """
    water_level1, x1 = water_levels2(turn=1)
    dike_level1, x2 = dike_levels(turn=1)
    fig, ax = plot_water_levels(x1, water_level1, turn=1)
    fig, ax = plot_water_levels(x2, dike_level1, turn=10, fig=fig, ax=ax)
    """
    return


if __name__ == "__main__":
    main()