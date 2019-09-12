# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


import os
import geojson
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import gridMapping as gridmap
from shapely import geometry
from os.path import join, dirname, realpath


class Water():
    def __init__(self):
        super(Water, self).__init__()
        self.x_grid = []
        self.initial_water_levels = []
        self.intervention_water_levels = []
        self.x_hexagons = []
        self.dike_levels = []
        self.bed_levels = []
        self.set_dirs()
        self.north_dike = None
        self.south_dike = None
        self.flood_safety_score = 0
        return
    
    def set_dirs(self):
        root_dir = dirname(realpath(__file__))
        self.web_dir = join(root_dir, 'webserver')
        return
    
    def determine_dike_levels(self, hexagons):
        dike_level_columns = [[] for i in range(15)]
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if (feature.properties["north_dike"] or
                feature.properties["south_dike"]):
                #dike_level = feature.properties["z"] - feature.properties["bedslope_correction"]
                dike_level = feature.properties["z_reference"] * 4 + feature.properties["bedslope_correction"]
                column = feature.properties["column"] - 1
                dike_level_columns[column].append(dike_level)
        dike_level = []
        for values in dike_level_columns:
            dike_height = min(values)
            #formatted = [ '%.2f' % elem for elem in values ]
            #print("water level values:", formatted, "average:", average)
            dike_level.append(round(dike_height, 2))
        self.dike_levels = np.flip(dike_level, 0)
        return
    
    def determine_bed_levels(self, hexagons):
        bed_level_columns = [[] for i in range(15)]
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if feature.properties["main_channel"]:
                #dike_level = feature.properties["z"] - feature.properties["bedslope_correction"]
                bed_level = feature.properties["bedslope_correction"]
                column = feature.properties["column"] - 1
                bed_level_columns[column].append(bed_level)
        bed_level = []
        for values in bed_level_columns:
            bed_level_min = min(values)
            #formatted = [ '%.2f' % elem for elem in values ]
            #print("water level values:", formatted, "average:", average)
            bed_level.append(round(bed_level_min, 2))
        self.bed_levels = np.flip(bed_level, 0)
        return
    
    def determine_x_hexagons(self):
        x_values = []
        for i in range(len(self.dike_levels)):
            x_values.append(i * 250)
        self.x_hexagons = x_values
        return
    
    def grid_river_axis_water_levels(self, grid, model, turn=0, save=False):
        """
        This function returns the water levels on the river axis.
        """
        def get_average(s1_list):
            average_list = []
            for values in s1_list:
                try:
                    average = sum(values) / len(values)
                    average_list.append(average)
                except ZeroDivisionError:
                    continue
            return average_list
        s1 = model.get_var('s1')
        columns = []
        # there are 133 columns, not all are filled
        model_output = [[] for i in range(134)]
        for feature in grid.features:
            if not feature.properties["river_axis"]:
                continue
            s = s1[feature.id]
            #s = feature.properties["water_level"]
            feature.properties["water_level"] = s
            column = feature.properties["column"]
            columns.append(column)
            model_output[column].append(s)
        #max_columns = max(columns)
        #x_output = [i for i in range(max_columns+1)]
        s1_output = get_average(model_output)
        if save:
            with open('river_axis_grid.geojson', 'w') as f:
                geojson.dump(grid, f, sort_keys=True, indent=2)
        if turn == 0:
            self.initial_water_levels = np.flip(s1_output, 0)
        else:
            self.intervention_water_levels = np.flip(s1_output, 0)
        return grid
    
    def determine_x_grid(self):
        x_values = []
        for i in range(len(self.initial_water_levels)):
            x_values.append(i * 30)
        self.x_grid = x_values
        return

    def get_dike_location(self, hexagons):
        def create_dikes(coor, z_values):
            dike_lines = []
            for i, xy in enumerate(coor):
                try:
                    xy_new = [i * -1 for i in xy]
                    z_this = z_values[i]
                    xy_next = coor[i+1]
                    xy_next_new = [i * -1 for i in xy_next]
                    z_next = z_values[i+1]
                except IndexError:
                    continue
                z = (z_this + z_next) / 2
                line = geojson.LineString([xy_new, xy_next_new])
                dike_segment = geojson.Feature(id=i, geometry=line)
                dike_segment.properties["z"] = z
                dike_lines.append(dike_segment)
            dike_lines = geojson.FeatureCollection(dike_lines)
            return dike_lines
        north_dike = []
        south_dike = []
        z_north = []
        z_south = []
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if feature.properties["north_dike"]:
                shape = geometry.asShape(feature.geometry)
                x = shape.centroid.x
                y = shape.centroid.y
                north_dike.append([x, y])
                z_north.append(feature.properties["z"])
            elif feature.properties["south_dike"]:
                shape = geometry.asShape(feature.geometry)
                x = shape.centroid.x
                y = shape.centroid.y
                south_dike.append([x, y])
                z_south.append(feature.properties["z"])
        self.north_dike = create_dikes(north_dike, z_north)
        self.south_dike = create_dikes(south_dike, z_south)
        return
    
    def index_dikes(self, grid):
        def add_columns(dikes, x_coor, columns):
            for feature in dikes.features:
                points = feature.geometry["coordinates"]
                pts1 = points[0]
                pts2 = points[1]
                x1 = pts1[0]
                x2 = pts2[0]
                column_list = []
                for i, x in enumerate(x_coor):
                    if x1 >= x >= x2:
                        column_list.append(columns[i])
                column_array = np.array(column_list)
                column_array = np.unique(column_array)
                feature.properties["grid_columns"] = column_array.tolist()
            return dikes
        x_coor = []
        columns = []
        for feature in grid.features:
            if not feature.properties["river_axis"]:
                continue
            point = feature.geometry["coordinates"]
            column = feature.properties["column"]
            x_coor.append(point[0])
            columns.append(column)
        self.north_dike = add_columns(self.north_dike, x_coor, columns)
        self.south_dike = add_columns(self.south_dike, x_coor, columns)
        return
    
    def determine_dike_water_level(self, turn=0, save=False):
        def water_levels_to_dike(dikes, water_levels):
            deduct = dikes.features[-1].properties["grid_columns"][0]
            for feature in dikes.features:
                dike_water_level = []
                for i in feature.properties["grid_columns"]:
                    dike_water_level.append(water_levels[i-deduct])
                average = sum(dike_water_level) / len(dike_water_level)
                feature.properties["water_level"] = average
                feature.properties["difference"] = (
                        feature.properties["z"] - average)
            return dikes
        if turn == 0:
            water_levels = self.initial_water_levels
        else:
            water_levels = self.intervention_water_levels
        self.north_dike = water_levels_to_dike(self.north_dike, water_levels)
        self.south_dike = water_levels_to_dike(self.south_dike, water_levels)
        if save:
            with open('north_dike_water_levels.geojson', 'w') as f:
                geojson.dump(self.north_dike, f, sort_keys=True, indent=2)
            with open('south_dike_water_levels.geojson', 'w') as f:
                geojson.dump(self.south_dike, f, sort_keys=True, indent=2)
        return
    
    def determine_flood_safety_score(self):
        score = 0
        multiplier = 1 / (len(self.north_dike.features) * 2)
        for feature in self.north_dike.features:
            if feature.properties["difference"] < 0.5:
                segment_score = 0
            elif feature.properties["difference"] < 1:
                segment_score = 0.5 * multiplier
            else:
                segment_score = multiplier
            score += segment_score
        for feature in self.south_dike.features:
            if feature.properties["difference"] < 0.5:
                segment_score = 0
            elif feature.properties["difference"] < 1:
                segment_score = 0.5 * multiplier
            else:
                segment_score = multiplier
            score += segment_score
        self.flood_safety_score = score
        print("flood safety score = " + str(score))
        return
    
    def get_flood_safety_score(self):
        return self.flood_safety_score

    def water_level_graph(self):
        plt.ioff()
        fig, ax = plt.subplots()
        if len(self.initial_water_levels) > 0:
            label = "initial water levels"
            ini_water_levels = ax.plot(self.x_grid, self.initial_water_levels, label=label)
        if len(self.intervention_water_levels) > 0:
            label = "current water levels"
            new_water_levels = ax.plot(self.x_grid, self.intervention_water_levels, label=label)
        if len(self.dike_levels) > 0:
            label = "dike levels"
            dike_levels = ax.plot(self.x_hexagons, self.dike_levels, label=label)
        legend = ax.legend(loc='best', facecolor='black', edgecolor='w',
                           fancybox=True, framealpha=0.5, fontsize="large")
        plt.setp(legend.get_texts(), color='w')
        ax.set_xlabel("river section (m)")
        ax.set_ylabel("height (m)")
        ax.set_title("Water levels on river axis")
        ax.spines['bottom'].set_color('w')
        ax.spines['top'].set_color('w') 
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('w')
        #ax.ticklabel_format(axis='y', style='sci', scilimits=(6,6))
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        ax.yaxis.label.set_color('w')
        ax.yaxis.label.set_fontsize(14)
        ax.xaxis.label.set_color('w')
        ax.xaxis.label.set_fontsize(14)
        ax.title.set_fontsize(20)
        ax.title.set_color('w')
        plt.tight_layout()
        plt.savefig(join(self.web_dir, "flood_safety_score1.png"), edgecolor='w',transparent=True)
        return
    
    def dike_safety_graph(self):
        plt.ioff()
        fig, ax = plt.subplots()
        if self.north_dike:
            for feature in self.north_dike.features:
                points = feature.geometry["coordinates"]
                x = [points[0][0],points[1][0]]
                y = [points[0][1],points[1][1]]
                if feature.properties["difference"] < 0.5:
                    color = 'r'
                elif feature.properties["difference"] < 1:
                    color = 'y'
                else:
                    color = 'g'
                ax.plot(x, y, color=color, linewidth=3.0)
        if self.south_dike:
            for feature in self.south_dike.features:
                points = feature.geometry["coordinates"]
                x = [points[0][0],points[1][0]]
                y = [points[0][1],points[1][1]]
                if feature.properties["difference"] < 0.5:
                    color = 'r'
                elif feature.properties["difference"] < 1:
                    color = 'y'
                else:
                    color = 'g'
                ax.plot(x, y, color=color, linewidth=3.0)
        red_patch = mpatches.Patch(color='r', label='1/500')
        yellow_patch = mpatches.Patch(color='y', label='1/1000')
        green_patch = mpatches.Patch(color='g', label='1/1250')
        
        legend = ax.legend(handles=[red_patch, yellow_patch, green_patch],
                           loc='best', facecolor='black', edgecolor='w',
                           fancybox=True, framealpha=0.5, fontsize="large")
        plt.setp(legend.get_texts(), color='w')
        ax.set_xlabel("river section x")
        ax.set_ylabel("river section y")
        ax.set_title("Dike segment flooding chances")
        ax.spines['bottom'].set_color('w')
        ax.spines['top'].set_color('w') 
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('w')
        #ax.ticklabel_format(axis='y', style='sci', scilimits=(6,6))
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        ax.yaxis.label.set_color('w')
        ax.yaxis.label.set_fontsize(14)
        ax.xaxis.label.set_color('w')
        ax.xaxis.label.set_fontsize(14)
        ax.title.set_fontsize(20)
        ax.title.set_color('w')
        plt.tight_layout()
        plt.savefig(join(self.web_dir, "flood_safety_score2.png"), edgecolor='w',transparent=True)
        return

def load(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    return hexagons


def load_grid(turn=0):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='river_axis_grid%d.geojson' % turn,
            path=test_path)
    return hexagons


def main():
    # this test will give errors as the grid_river_axis_water_levels function
    # requires a model input, which is only there on full runs.
    water_module = Water()
    turn = 0
    hexagons = load(turn=turn)
    water_module.determine_dike_levels(hexagons)
    water_module.get_dike_location(hexagons)
    face_grid = load_grid(turn=turn)
    water_module.index_dikes(face_grid)
    water_module.determine_dike_water_level(turn=turn)
    """
    face_grid = load_grid(turn=turn)
    water_module.determine_dike_levels(hexagons)
    water_module.determine_x_hexagons()
    face_grid = gridmap.determine_grid_river_axis(hexagons, face_grid)
    water_module.grid_river_axis_water_levels(face_grid, turn=turn)
    water_module.determine_x_grid()
    turn = 1
    hexagons = load(turn=turn)
    face_grid = load_grid(turn=turn)
    water_module.determine_dike_levels(hexagons)
    face_grid = gridmap.determine_grid_river_axis(hexagons, face_grid)
    water_module.grid_river_axis_water_levels(face_grid, turn=turn)
    water_module.water_level_graph()
    """
    return

if __name__ == '__main__':
    main()