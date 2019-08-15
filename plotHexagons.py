# -*- coding: utf-8 -*-
"""
Created on Mon May  6 16:27:14 2019

@author: HaanRJ
"""

import cv2
import geojson
import numpy as np
import matplotlib.pyplot as plt
from descartes import PolygonPatch


def visualize_ownership(hexagons):
    # generate empty, white image
    img = np.full((450, 600, 3), 255, dtype="uint8")
    # draw hexagons in empty image
    for feature in hexagons.features:
        # skip hexagons that do not need to be drawn
        if (feature.properties["ghost_hexagon"] or
            feature.properties["behind_dike"] or 
            feature.properties["south_dike"] or
            feature.properties["north_dike"] or
            feature.properties["main_channel"]):
            continue
        # set color to draw based on ownership (or lack of it)
        if feature.properties["owner"] == "Water":
            color = (241, 96, 52)
        elif feature.properties["owner"] == "Nature":
            color = (31, 127, 63)
        elif feature.properties["owner"] == "Province":
            color = (66, 28, 213)
        else:
            color = (160, 160, 160)
        
        # get the coordinates to draw the hexagons, turn into numpy array and
        # add the necessary offset to match
        pts = feature.geometry["coordinates"]
        pts = np.array(pts)
        pts = pts + [400, 300]
        pts = pts * [0.75, 0.75]
        pts = pts.astype(np.int32)
        cv2.fillPoly(img, pts, color)
    cv2.imshow('Window', img)
    return img

    
def plot_elevation2(hexagons, turn=0):
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
        test = PolygonPatch(poly, fc=color, ec=color, alpha=0.5, zorder=2)
        if hexagon.id == 0:
            print(test)
        ax.add_patch(test)
    ax.axis('scaled')
    plt.show()
    
    
def plot_ownership(hexagons, turn=0):
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
        with open('storing_files\\hexagons0.geojson') as f:
            hexagons0 = geojson.load(f)
        img = visualize_ownership(hexagons0)
    except FileNotFoundError:
        pass
    """
    try:
        with open('test_files\\hexagons4.geojson') as f:
            hexagons1 = geojson.load(f)
        plot(hexagons1, turn=4)
    except FileNotFoundError:
        pass
    try:
        with open('test_files\\hexagons5.geojson') as f:
            hexagons2 = geojson.load(f)
        plot(hexagons2, turn=5)
    except FileNotFoundError:
        pass
    try:
        with open('test_files\\hexagons6.geojson') as f:
            hexagons3 = geojson.load(f)
        plot(hexagons3, turn=6)
    except FileNotFoundError:
        pass
    """
