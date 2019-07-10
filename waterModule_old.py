# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


import os
import matplotlib.pyplot as plt
import gridMapping as gridmap
from shapely import geometry


class Water_module():  
    def __init__(self):
        super(Water_module, self).__init__()
        self.initial_water_level = None
        self.new_water_levels = []
        #self.set_variables()

    def set_variables(self):
        return
    
    
    def water_levels(self, hexagons):
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
    
    
    def plot_water_levels(self, xvals, yvals, turn=0, fig=None, ax=None):
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


def main():
    turn = 0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn, path=test_path)
    water = Water_module()
    water_level, x_output = water.water_levels(hexagons)
    fig, ax = water.plot_water_levels(x_output, water_level, turn=turn)


if __name__ == '__main__':
    main()