# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 18:24:08 2019

@author: HaanRJ
"""

import numpy as np
from cv2 import fillPoly


def visualize_ownership(hexagons, end_of_round=False):
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
        if end_of_round:
            if feature.properties["owner"] == "Water":
                color = (52, 96, 241)
            elif feature.properties["owner"] == "Nature":
                color = (31, 127, 63)
            elif feature.properties["owner"] == "Province":
                color = (213, 28, 66)
            else:
                color = (160, 160, 160)
        else:
            if feature.properties["ownership_change"]:
                color = (235, 232, 4)
            elif feature.properties["owner"] == "Water":
                color = (52, 96, 241)
            elif feature.properties["owner"] == "Nature":
                color = (31, 127, 63)
            elif feature.properties["owner"] == "Province":
                color = (213, 28, 66)
            else:
                color = (160, 160, 160)
        
        # get the coordinates to draw the hexagons, turn into numpy array and
        # add the necessary offset to match
        pts = feature.geometry["coordinates"]
        pts = np.array(pts)
        pts = pts * [0.94, 1]
        pts = pts + [395, 300]
        pts = pts * [0.75, 0.75]
        pts = np.round_(pts)
        pts = pts.astype(np.int32)

        # draw the hexagon as a filled polygon
        fillPoly(img, pts, color)
    return img


def visualize_prev_turn(hexagons):
    # generate empty, white image
    img = np.full((450, 600, 3), 255, dtype="uint8")
    # draw hexagons in empty image
    for feature in hexagons.features:
        # skip hexagons that do not need to be drawn
        if feature.properties["ghost_hexagon"]:
            continue
        # set color to draw based on ownership (or lack of it)
        if feature.properties["z_reference"] == 0:
            color = (17, 14, 196)
        elif feature.properties["z_reference"] == 1:
            color = (14, 187, 196)
        elif feature.properties["z_reference"] == 2:
            color = (17, 138, 43)
        elif feature.properties["z_reference"] == 3:
            color = (224, 227, 20)
        elif feature.properties["z_reference"] == 4:
            color = (255, 144, 144)
        else:
            color = (214, 17, 17)
        
        # get the coordinates to draw the hexagons, turn into numpy array and
        # add the necessary offset to match
        pts = feature.geometry["coordinates"]
        pts = np.array(pts)
        pts = pts * [0.94, 1]
        pts = pts + [395, 300]
        pts = pts * [0.75, 0.75]
        pts = np.round_(pts)
        pts = pts.astype(np.int32)
        
        """
        TO DO: add icons or something for land use
        """

        # draw the hexagon as a filled polygon
        fillPoly(img, pts, color)
    return img