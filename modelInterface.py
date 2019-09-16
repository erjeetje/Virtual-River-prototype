# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:21:54 2019

@author: HaanRJ
"""


import os
import time
import bmi.wrapper
import numpy as np
import updateRoughness as roughness
from shapely import geometry

class Model():
    def __init__(self):
        self.model = self.initialize_model()
        self.fig = None
        self.axes = None
        self.node_index = None
        self.face_index = None
        return

    def initialize_model(self):
        """
        Function to initialize the model using bmi. If the Virtual River is copied
        including the models folder, no changes are needed.
        """
        model = bmi.wrapper.BMIWrapper('dflowfm')
        dir_path = os.path.dirname(os.path.realpath(__file__))
        model_name = 'Virtual_River.mdu'
        model_path = os.path.join(dir_path, 'models', 'Waal_schematic', model_name)
        model.initialize(model_path)
        print('Initialized Delft3D FM model.')
        return model

    def set_indexes(self, node_grid, face_grid):
        """
        Get the locations of the node and grid cells and store them as indexes
        that can be used when drawing from model output (to only get the game
        board model output).
        """
        def index(grid):
            x_left_board = -400
            x_right_board = 400
            y_bottom_board = -300
            x_top_board = 300
            indexes = []
            for feature in grid.features:
                shape = geometry.asShape(feature.geometry)
                x = shape.centroid.x
                y = shape.centroid.y
                if ((x >= x_left_board and x <= x_right_board) and
                    (y >= y_bottom_board and y <= x_top_board)):
                    indexes.append(feature.id)
            return indexes
        self.node_index = np.array(index(node_grid))
        self.face_index = np.array(index(face_grid))
        return

    def run_model(self, filled_node_grid, hexagons, flow_grid, turn=0):
        """
        This function runs the hydrodynamic model updates. It runs updates in
        loops and breaks the loop when a new equilibrium is found (or rather.
        when the model is close to one).
        """

        # get only the new z points of the node grid that require to be updated
        changed = [
                feature
                for feature
                in filled_node_grid.features
                if feature.properties['changed']
        ]

        # for every z in changed, update the 'zk' variable of the model.
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64')
            self.model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
                    )
        print("updated grid in model")

        # set the maximum amount of update loops. 50 loops on initialization
        # makes sure that there are little to no stabilizing effects in later
        # turns.
        if turn == 0:
            step = 50
        else:
            step = 10
        i = 0
        stable = 0
        
        # update the roughness values once before running the model.
        self.update_waterlevel(hexagons)
        hexagons = roughness.landuse_to_friction(hexagons)
        hexagons, flow_grid = roughness.hex_to_points(
                self.model, hexagons, flow_grid)
        
        while i < step:
            t0 = time.time()
            # run a model update.
            self.model.update(125)

            # update the roughness on every loop.
            self.update_waterlevel(hexagons)
            hexagons = roughness.landuse_to_friction(hexagons)
            hexagons, flow_grid = roughness.hex_to_points(
                    self.model, hexagons, flow_grid)

            # get the water levels from before and after the model.update for
            # all the face cells within that are within the game board.
            d = (self.model.get_var('s1')[self.face_index] -
                 self.model.get_var('s0')[self.face_index])

            # get the mean and maximum difference between the water levels
            # before and after updating.
            mean = abs(np.mean(d))
            diff = max(abs(d))
            print("Loop mean: " + str(mean) + ". Loop difference: " + str(diff))
            t1 = time.time()

            if (mean < 0.00025 and diff < 0.0075):
                # we want to break the loop when there is little difference between
                # the water levels before and after an update, both on average
                # (mean) and max (diff).
                if turn == 0:
                    # we want to run the initialization rather long to make sure
                    # we don't see additional effects of moving to an equilibrium
                    # during updates. Therefore a pass statement.
                    pass
                else:
                    # note a stable loop during updates if mean and diff
                    # conditions are met.
                    stable += 1
                    print("Stable model loops: " + str(stable))
                if stable > 2:
                    # break when tree stable loops have occured (thus also
                    # a minimum of three update loops).
                    print("Ending loop: Obtained a new equilibrium after " +
                          str(i+1) + " loops. Last loop time: " + str(t1 - t0))
                    break
            i += 1
            print("model update: " + str(t1 - t0))
            print("Executed model loop " + str(i) +
                  ", roughness updated. Loop time: " + str(t1 - t0))
        print("Finished run model. Current time in model: " +
              str(self.model.get_current_time()))
        return hexagons, flow_grid

    def update_waterlevel(self, hexagons):
        """
        Update the water level at the center of each hexagon so that the new
        roughness coefficient for the hexagon can be calculated.
        """
        s1 = self.model.get_var('s1')
        for feature in hexagons.features:
            index = feature.properties["face_cell"]
            feature.properties["water_level"] = s1[index]
        return hexagons

    def update_waterlevel_new(self, hexagons):
        """
        Update the water level at the center of each hexagon so that the new
        roughness coefficient for the hexagon can be calculated.
        
        This version of the function included the crosssections which are no
        longer used. Function is therefore not called.
        """
        s1 = self.model.get_var('s1')
        for feature in hexagons.features:
            index = feature.properties["face_cell"]
            feature.properties["water_level"] = s1[index]
            if feature.properties["ghost_hexagon"]:
                continue
            if feature.properties["main_channel"]:
                feature.properties["water_levels"] = []
                indexes = feature.properties["crosssection"]
                for index in indexes:
                    feature.properties["water_levels"].append(s1[index])
        return hexagons


def main():
    return


if __name__ == "__main__":
    main()
