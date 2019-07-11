# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


import os
import numpy as np
import matplotlib.pyplot as plt
import gridMapping as gridmap
from shapely import geometry


def water_levels(hexagons):
    water_level_columns = [[] for i in range(15)]
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["behind_dike"] or
            feature.properties["north_dike"] or
            feature.properties["south_dike"]):
            continue
        else:
            water_level = feature.properties["water_level"] - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(water_level)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    return water_level


def dike_levels(hexagons):
    water_level_columns = [[] for i in range(15)]
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"]):
            dike_level = feature.properties["z"] - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(dike_level)
    dike_level = []
    for values in water_level_columns:
        dike_height = min(values)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        dike_level.append(round(dike_height, 1))
    return dike_level

def get_river_length(water_levels):
    x_values = []
    for i in range(len(water_levels)):
        x_values.append(i * 250)
    return x_values


def get_river_length2(hexagons):
    x_values = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"]):
            shape = geometry.asShape(feature.geometry)
            x_hex = shape.centroid.x
            x_values.append(x_hex)
    x_output = []
    for x in x_values:
        x = round(x, 2)
        if x not in x_output:
            x_output.append(x)
    return x_output


def flood_safety(dike_levels, water_levels):
    z_difference = [(i - j) for i, j in zip(dike_levels, water_levels)]
    divide = int(round(len(z_difference) / 3))
    avg_sections = []
    #z_difference = [(i+1) for i in range (0, 15)]
    avg_left = sum(z_difference[:divide]) / divide
    avg_middle = sum(z_difference[divide:divide*2]) / divide
    avg_right = sum(z_difference[divide*2:]) / divide
    
    #print(z_difference)
    #print(z_difference[:divide])
    #print(z_difference[divide:divide*2])
    #print(z_difference[divide*2:])
    
    avg_sections.append(avg_left)
    avg_sections.append(avg_middle)
    avg_sections.append(avg_right)
    
    flood_safety_levels = []
    for average in avg_sections:
        if average < -1:
            flood_safety = 100
        elif average < -0.5:
            flood_safety = 200
        elif average < 0:
            flood_safety = 400
        elif average < 0.25:
            flood_safety = 600
        elif average < 0.5:
            flood_safety = 800
        elif average < 0.75:
            flood_safety = 1000
        else:
            flood_safety = 1250
        flood_safety_levels.append(flood_safety)

    print(flood_safety_levels)
    return flood_safety_levels

def plot_water_levels(xvals, yvals, turn=0, fig=None, ax=None):
    xvals = []
    for i in range(len(yvals)):
        xvals.append(i * 250)
    if fig is None:
        fig, ax = plt.subplots(1)
        ax.set_xlabel('river section (meters)')
        ax.set_ylabel('water levels (meters)')
    if turn == 0:
        label = "initial board"
    else:
        label = ("board after turn " + str(turn))
    ax.plot(xvals, yvals, label=label)
    ax.legend(loc='upper right')
    plt.show
    return fig, ax

def load(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'storing_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    return hexagons


def main():
    """turn = 0
    hexagons = load(turn=turn)
    water_level, x_output = water_levels(hexagons)
    dike_level, x_output = dike_levels(hexagons)
    fig, ax = plot_water_levels(x_output, water_level, turn=turn)
    fig, ax = plot_water_levels(x_output, dike_level, turn=turn, fig=fig,
                                ax=ax)
    """
    dike_levels = [5 for i in range(0, 15)]
    water_levels = [4 for i in range (0, 15)]
    flood_safety_levels = flood_safety(dike_levels, water_levels)
    return

if __name__ == '__main__':
    main()