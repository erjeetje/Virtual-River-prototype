# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 18:24:08 2019

@author: HaanRJ
"""

import os
import numpy as np
from cv2 import (fillPoly, imread, IMREAD_UNCHANGED, split, merge, multiply,
                 add, flip)  #, imshow, cvtColor, COLOR_BGR2RGB)
#from geojson import load
from shapely import geometry

class createViz():
    def __init__(self):
        super(createViz, self).__init__()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.image_path = os.path.join(dir_path, 'icon_files')
        self.store_icons()
        return

    def store_icons(self):
        # load and store all the icons when starting up
        self.factory_icon, self.factory_alpha = self.get_icon("factory.png")
        self.farm_icon, self.farm_alpha = self.get_icon("farm.png")
        self.meadow_icon, self.meadow_alpha = self.get_icon("meadow.png")
        self.grassland_icon, self.grassland_alpha = (
                self.get_icon("grassland.png"))
        self.reed_icon, self.reed_alpha = self.get_icon("reed.png")
        self.shrubs_icon, self.shrubs_alpha = self.get_icon("shrubs.png")
        self.forest_icon, self.forest_alpha = self.get_icon("forest.png")
        self.mixtype_icon, self.mixtype_alpha = self.get_icon("mixtype.png")
        self.sidechannel_icon, self.sidechannel_alpha = (
                self.get_icon("sidechannel.png"))
        self.ltd_icon, self.ltd_alpha = self.get_icon("ltd.png")
        #self.groyne_icon = self.get_icon("groyne.png")  # no groyne icon
        self.dike_icon, self.dike_alpha = self.get_icon("dike.png")
        return

    def get_icon(self, name):
        path = os.path.join(self.image_path, name)
        icon = imread(path, IMREAD_UNCHANGED)
        icon = flip(icon, -1)
        b, g, r, alpha = split(icon)
        icon = merge((b, g, r))
        icon = icon.astype(float)
        alpha = merge((alpha, alpha, alpha))
        alpha = alpha.astype(float)/255
        return icon, alpha

    def visualize_ownership(self, hexagons, end_of_round=False):
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

            # get the coordinates to draw the hexagons, turn into numpy array
            # and add the necessary offset to match
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

    def visualize_prev_turn(self, hexagons):
        # generate empty, white image
        img = np.full((450, 600, 3), 255, dtype="uint8")
        # draw hexagons in empty image
        for feature in hexagons.features:
            # skip hexagons that do not need to be drawn
            if feature.properties["ghost_hexagon"]:
                continue
            # set color to draw based on the hexagon's elevation
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

            # get the coordinates to draw the hexagons, turn into numpy array
            # and add the necessary offset to match
            pts = feature.geometry["coordinates"]
            pts = np.array(pts)
            pts = pts * [0.94, 1]
            pts = pts + [395, 300]
            pts = pts * [0.75, 0.75]
            pts = np.round_(pts)
            pts = pts.astype(np.int32)

            # draw the hexagon as a filled polygon to show elevation
            fillPoly(img, pts, color)

            # get the midpoint of the hexagon, offset correctly (same as above)
            midpoint = geometry.asShape(feature.geometry)
            xy = np.array([midpoint.centroid.x, midpoint.centroid.y])
            xy = xy * [0.94, 1]
            xy = xy + [395, 300]
            xy = xy * [0.75, 0.75]
            xy = np.round_(xy)
            xy = xy.astype(np.int32)

            # get the x, y coordinates to change in the image
            X, Y = np.mgrid[xy[0]-10:xy[0]+9:20j, xy[1]-17:xy[1]+2:20j]
            positions = np.vstack([X.ravel(), Y.ravel()]).T
            positions = positions.astype(np.int32)
            I, J = np.transpose(positions)
            I_copy = I - min(I)
            J_copy = J - min(J)

            # determine which icon to use in the image
            icon = None
            
            if feature.properties["landuse"] == 0:
                if feature.properties["factory"]:
                    icon = self.factory_icon.copy()
                    icon_alpha = self.factory_alpha.copy()
                else:
                    icon = self.farm_icon.copy()
                    icon_alpha = self.farm_alpha.copy()
            elif feature.properties["landuse"] == 1:
                icon = self.meadow_icon.copy()
                icon_alpha = self.meadow_alpha.copy()
            elif feature.properties["landuse"] == 2:
                icon = self.grassland_icon.copy()
                icon_alpha = self.grassland_alpha.copy()
            elif feature.properties["landuse"] == 3:
                icon = self.reed_icon.copy()
                icon_alpha = self.reed_alpha.copy()
            elif feature.properties["landuse"] == 4:
                icon = self.shrubs_icon.copy()
                icon_alpha = self.shrubs_alpha.copy()
            elif feature.properties["landuse"] == 5:
                icon = self.forest_icon.copy()
                icon_alpha = self.forest_alpha.copy()
            elif feature.properties["landuse"] == 6:
                icon = self.mixtype_icon.copy()
                icon_alpha = self.mixtype_alpha.copy()
            elif feature.properties["landuse"] == 7:
                icon = self.sidechannel_icon.copy()
                icon_alpha = self.sidechannel_alpha.copy()
            elif feature.properties["landuse"] == 8:
                icon = self.ltd_icon.copy()
                icon_alpha = self.ltd_alpha.copy()
            """
            # currently not adding groyne or dike icons, groynes are clear
            # from ltds (and ltds will never be implemented twice) and dikes
            # are clear from elevation
            elif feature.properties["landuse"] == 9:
                icon = self.groyne_icon.copy()
                icon_alpha = self.groyne_alpha.copy()
            elif (feature.properties["landuse"] == 10 and
                  feature.properties["z_reference"] == 4):
                icon = self.dike_icon.copy()
                icon_alpha = self.dike_alpha.copy()
            """

            # if there is an icon to draw, do something, else loop ends
            if icon is not None:
                # create a background from the hexagon elevation color
                background = np.full((20, 20, 3), color, dtype="float64")
                
                # adjust the icon and background colors according to the alpha
                icon = multiply(icon_alpha, icon)
                background = multiply(1.0 - icon_alpha, background)
                
                # merge the icon with the background
                merged = add(icon, background)
                
                # change the pixels in the main image to match the icon
                for i, coor in enumerate(zip(J, I)):
                    img[coor] = merged[J_copy[i], I_copy[i]]
            
        #imshow('image', cvtColor(img, COLOR_BGR2RGB))
        return img

def main():
    """ 
    viz = createViz()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'storing_files')
    with open(os.path.join(test_path, "hexagons0.geojson")) as f:
        hexagons = load(f)
    img = viz.visualize_prev_turn(hexagons)
    """
    return

if __name__ == '__main__':
    main()