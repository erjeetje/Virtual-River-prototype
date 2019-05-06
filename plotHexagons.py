# -*- coding: utf-8 -*-
"""
Created on Mon May  6 16:27:14 2019

@author: HaanRJ
"""


import geojson
import matplotlib.pyplot as plt
from descartes import PolygonPatch


def plot(hexagons, turn=0):
    blue = '#32618f'
    light_blue = '#66ccf2'
    yellow = '#f6eb34'
    orange = '#f79f14'
    red = '#e31e1e'
    fig = plt.figure()
    ax = fig.gca()
    plt.title('Board turn ' + str(turn))
    for hexagon in hexagons.features:
        poly = hexagon.geometry
        if hexagon.properties["z"] <= 0.5:
            color = blue
        elif hexagon.properties["z"] <= 1.5:
            color = light_blue
        elif hexagon.properties["z"] <= 2.5:
            color = yellow
        elif hexagon.properties["z"] <= 3.5:
            color = orange
        else:
            color = red
        ax.add_patch(PolygonPatch(poly, fc=color, ec=color, alpha=0.5,
                                  zorder=2))
    ax.axis('scaled')
    plt.show()


if __name__ == '__main__':
    try:
        with open('hexagons0.geojson') as f:
            hexagons0 = geojson.load(f)
        plot(hexagons0, turn=0)
    except FileNotFoundError:
        pass
    try:
        with open('hexagons1.geojson') as f:
            hexagons1 = geojson.load(f)
        plot(hexagons1, turn=1)
    except FileNotFoundError:
        pass
    try:
        with open('hexagons2.geojson') as f:
            hexagons2 = geojson.load(f)
        plot(hexagons2, turn=2)
    except FileNotFoundError:
        pass
    try:
        with open('hexagons3.geojson') as f:
            hexagons3 = geojson.load(f)
        plot(hexagons3, turn=3)
    except FileNotFoundError:
        pass
