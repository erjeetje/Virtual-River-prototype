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
        # variables stored to draw the figures.
        self.x_grid = []
        self.initial_water_levels = []
        self.intervention_water_levels = []
        self.x_hexagons = []
        self.dike_levels = []
        self.bed_levels = []
        # the shapes of the dikes (geojson featurecollection) and river axis
        # (geojson feature).
        self.north_dike = None
        self.south_dike = None
        self.river_axis = None
        # flood safety score, set by the determine_flood_safety_score function.
        self.flood_safety_score = 0
        # lowest and hightest grid columns that are used to calculate the
        # river axis water levels. Values are updated by the functions.
        self.lowest_column = 50
        self.highest_column = 50
        # variables that determine the range for the difference in water levels
        # and dike crest height contributing to a 'bad', 'adequate', and 'good'
        # score.
        self.unsafe = 0.25
        self.safer = 0.5
        # save the directories used to store the figures.
        self.set_dirs()
        return
    
    def set_dirs(self):
        root_dir = dirname(realpath(__file__))
        self.web_dir = join(root_dir, 'webserver')
        return
    
    def determine_dike_levels(self, hexagons):
        """
        Function that saves the dike crest height in the object variables.
        """
        dike_level_columns = [[] for i in range(15)]
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if (feature.properties["north_dike"] or
                feature.properties["south_dike"]):
                dike_level = (min(feature.properties["z_reference"] * 4, 17) +
                              feature.properties["bedslope_correction"])
                column = feature.properties["column"] - 1
                dike_level_columns[column].append(dike_level)
        dike_level = []
        for values in dike_level_columns:
            dike_height = min(values)
            dike_level.append(round(dike_height, 2))
        # in case the direction of the dikes in the figure needs to be
        # switched, switch the lines below.
        #self.dike_levels = np.flip(dike_level, 0)
        self.dike_levels = dike_level
        return
    
    def determine_bed_levels(self, hexagons):
        """
        Function that saves the river bed level height in the object variables.
        
        Function is currently not called in Virtual River.
        """
        bed_level_columns = [[] for i in range(15)]
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if feature.properties["main_channel"]:
                bed_level = feature.properties["bedslope_correction"]
                column = feature.properties["column"] - 1
                bed_level_columns[column].append(bed_level)
        bed_level = []
        for values in bed_level_columns:
            bed_level_min = min(values)
            bed_level.append(round(bed_level_min, 2))
        # in case the direction of the dikes in the figure needs to be
        # switched, switch the lines below.
        #self.bed_levels = np.flip(bed_level, 0)
        self.bed_levels = bed_level
        return
    
    def determine_x_hexagons(self):
        """
        Function that saves the x locations of the dike crest height values
        in the object variables.
        """
        x_values = []
        for i in range(len(self.dike_levels)):
            x_values.append(i * 250)
        self.x_hexagons = x_values
        return
    
    def determine_grid_river_axis(self, hexagons, grid, save=False):
        """
        This function determines cells that other functions should look at to get
        the water levels. Function is only called at the initialization of Virtual
        River.
        
        This version of the function finds a 'wider axis' and includes multiple
        cells for each crossection (cell columns).
        """
        def get_average(coor_list):
            average_list = []
            for values in coor_list:
                average = sum(values) / len(values)
                average_list.append(average)
            return average_list
        x_all = [[] for i in range(15)]
        y_all = [[] for i in range(15)]
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if not feature.properties["main_channel"]:
                continue
            shape = geometry.asShape(feature.geometry)
            x = shape.centroid.x
            y = shape.centroid.y
            column = feature.properties["column"] - 1
            x_all[column].append(x)
            y_all[column].append(y)
        x_coor = get_average(x_all)
        y_coor = get_average(y_all)
        xy = list(zip(x_coor, y_coor))
        line = geojson.LineString(xy)        
        self.river_axis = geojson.Feature(id=0, geometry=line)
        river_axis = geometry.asShape(line)
        columns_covered = []
        feature_ids = []
        for feature in grid.features:
            if feature.properties["column"] is None:
                continue
            point = geometry.asShape(feature.geometry)
            distance = point.distance(river_axis)
            # change the value to compare here to determine the width of the
            # river axis that is looked at. 6 means 2 to 3 cells per grid
            # column.
            if distance < 6:
                column = feature.properties["column"]
                columns_covered.append(column)
                feature_ids.append(feature.id)
        for feature in grid.features:
            if feature.properties["column"] is None:
                feature.properties["river_axis"] = False
                continue
            if feature.id in feature_ids:
                feature.properties["river_axis"] = True
            else:
                feature.properties["river_axis"] = False
        if save:
            with open('river_axis_grid_wide.geojson', 'w') as f:
                geojson.dump(grid, f, sort_keys=True, indent=2)
        return grid

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
        # there are 133 columns, not all are filled, this is filtered out in
        # the get_average function through the ZeroDivisionError errorhandler.
        model_output = [[] for i in range(134)]
        for feature in grid.features:
            if not feature.properties["river_axis"]:
                continue
            s = s1[feature.id]
            feature.properties["water_level"] = s
            column = feature.properties["column"]
            columns.append(column)
            model_output[column].append(s)
        s1_output = get_average(model_output)
        if save:
            with open('river_axis_grid.geojson', 'w') as f:
                geojson.dump(grid, f, sort_keys=True, indent=2)
        # in case the direction of the dikes in the figure needs to be
        # switched, switch the lines in the if/else statement below.
        if turn == 0:
            #self.initial_water_levels = np.flip(s1_output, 0)
            self.initial_water_levels = s1_output
        else:
            #self.intervention_water_levels = np.flip(s1_output, 0)
            self.intervention_water_levels = s1_output
        return grid
    
    def determine_x_grid(self):
        """
        Function that saves the x locations of the grid columns (supplying the
        data for the water levels graph) in the object variables.
        """
        x_values = []
        for i in range(len(self.initial_water_levels)):
            x_values.append(i * 30)
        self.x_grid = x_values
        return

    def get_dike_location(self, hexagons):
        """
        Function that determines how the dikes are positioned on the board and
        saves them in the object variables (as a geojson featurecollection).
        """
        def create_dikes(coor, z_values):
            dike_lines = []
            for i, xy in enumerate(coor):
                try:
                    # in case the direction of the dikes in the figure needs to
                    # be switched, use the xy_new and xy_next_new below.
                    #xy_new = [i * -1 for i in xy]
                    z_this = z_values[i]
                    xy_next = coor[i+1]
                    #xy_next_new = [i * -1 for i in xy_next]
                    z_next = z_values[i+1]
                except IndexError:
                    continue
                z = (z_this + z_next) / 2
                # in case the direction of the dikes in the figure needs to be
                # switched, switch the lines below.
                #line = geojson.LineString([xy_new, xy_next_new])
                line = geojson.LineString([xy, xy_next])
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
        """
        Function that indexes the dike locations, stores the indexes in the
        dike features (per segment).
        """
        def add_columns(dikes, x_coor, columns):
            columns_all = []
            for feature in dikes.features:
                points = feature.geometry["coordinates"]
                pts1 = points[0]
                pts2 = points[1]
                x1 = pts1[0]
                x2 = pts2[0]
                column_list = []
                for i, x in enumerate(x_coor):
                    # in case direction of graphs is flipped, change the < to >
                    if x1 <= x <= x2:
                        column_list.append(columns[i])
                        columns_all.append(columns[i])
                column_array = np.array(column_list)
                column_array = np.unique(column_array)
                feature.properties["grid_columns"] = column_array.tolist()
            return dikes, columns_all
        x_coor = []
        columns = []
        for feature in grid.features:
            if not feature.properties["river_axis"]:
                continue
            point = feature.geometry["coordinates"]
            column = feature.properties["column"]
            x_coor.append(point[0])
            columns.append(column)
        self.north_dike, columns_all = add_columns(self.north_dike, x_coor, columns)
        self.south_dike, columns_all = add_columns(self.south_dike, x_coor, columns)
        self.lowest_column = min(columns_all)
        self.highest_column = max(columns_all)
        return
    
    def determine_dike_water_level(self, turn=0, save=False):
        """
        Function that determines the difference between the dike crest height
        and corresponding water levels on the river axis (per dike segment).
        Water level and difference is stored in the dike segment features.
        """
        def water_levels_to_dike(dikes, water_levels, deduct=0):
            #deduct = dikes.features[0].properties["grid_columns"][0]
            for feature in dikes.features:
                dike_water_level = []
                for i in feature.properties["grid_columns"]:
                    try:
                        dike_water_level.append(water_levels[i-deduct])
                    except IndexError:
                        continue
                average = sum(dike_water_level) / len(dike_water_level)
                feature.properties["water_level"] = average
                feature.properties["difference"] = (
                        feature.properties["z"] - average)
            return dikes
        if turn == 0:
            water_levels = self.initial_water_levels
        else:
            water_levels = self.intervention_water_levels
        self.north_dike = water_levels_to_dike(self.north_dike, water_levels,
                                               deduct=self.lowest_column)
        self.south_dike = water_levels_to_dike(self.south_dike, water_levels,
                                               deduct=self.lowest_column)
        if save:
            with open('north_dike_water_levels.geojson', 'w') as f:
                geojson.dump(self.north_dike, f, sort_keys=True, indent=2)
            with open('south_dike_water_levels.geojson', 'w') as f:
                geojson.dump(self.south_dike, f, sort_keys=True, indent=2)
        return
    
    def determine_flood_safety_score(self):
        """
        Function to calculates the flood safety score. Score is calculated
        based on each dike segment (2*15 locations), where if the difference
        between the water level on the river axis and the dike height is
        smaller than 'self.unsafe', it counts as 0. In case the value is bigger
        than 'self.unsafe', but smaller than 'self.safer', it counts as 0.5. If
        it is bigger than 'self.safer', it counts as 1. Score is subsequently
        aggregated to between 0 and 1 total (based on 0 as lowest possible
        score and 1 as highest possible).
        """
        score = 0
        multiplier = 1 / (len(self.north_dike.features) * 2)
        for feature in self.north_dike.features:
            if feature.properties["difference"] < self.unsafe:
                segment_score = 0
            elif feature.properties["difference"] < self.safer:
                segment_score = 0.5 * multiplier
            else:
                segment_score = multiplier
            score += segment_score
        for feature in self.south_dike.features:
            if feature.properties["difference"] < self.unsafe:
                segment_score = 0
            elif feature.properties["difference"] < self.safer:
                segment_score = 0.5 * multiplier
            else:
                segment_score = multiplier
            score += segment_score
        self.flood_safety_score = score
        print("flood safety score = " + str(score))
        return
    
    def get_flood_safety_score(self):
        return self.flood_safety_score

    def get_dike_safety(self):
        red = 0
        yellow = 0
        green = 0
        if self.north_dike:
            for feature in self.north_dike.features:
                if feature.properties["difference"] < self.unsafe:
                    red += 1
                elif feature.properties["difference"] < self.safer:
                    yellow += 1
                else:
                    green += 1
        if self.south_dike:
            for feature in self.south_dike.features:
                if feature.properties["difference"] < self.unsafe:
                    red += 1
                elif feature.properties["difference"] < self.safer:
                    yellow += 1
                else:
                    green += 1
        return [red, yellow, green]
    
    
    def water_level_graph(self):
        """
        Function to draw the water level graph that is displayed in the flood
        safety indicator in Tygron.
        """
        plt.ioff()
        fig, ax = plt.subplots()
        # draw the initial board water levels in the figure
        if len(self.initial_water_levels) > 0:
            label = "initial water levels"
            ini_water_levels = ax.plot(
                    self.x_grid, self.initial_water_levels, label=label,
                    color='C1', linewidth=2)
        # draw the current board water levels in the figure
        if len(self.intervention_water_levels) > 0:
            label = "current water levels"
            new_water_levels = ax.plot(
                    self.x_grid, self.intervention_water_levels, label=label,
                    color='C0', linewidth=2)
        # draw the current dike height levels in the figure
        if len(self.dike_levels) > 0:
            label = "dike levels"
            dike_levels = ax.plot(
                    self.x_hexagons, self.dike_levels, label=label,
                    color='C3', linewidth=2)
            min_value = min(self.dike_levels) - 1.5
            max_value = max(self.dike_levels) - 1.5
            if len(self.intervention_water_levels) > 0:
                length = len(self.x_grid)
                line = np.linspace(max_value, min_value, num=length)
                ax.fill_between(self.x_grid, self.intervention_water_levels,
                                line, facecolor='C0', alpha=0.5)
            elif len(self.initial_water_levels) > 0:
                length = len(self.x_grid)
                line = np.linspace(max_value, min_value, num=length)
                ax.fill_between(self.x_grid, self.initial_water_levels,
                                line, facecolor='C0', alpha=0.5)
        # add the legend
        legend = ax.legend(loc='best', facecolor='black', edgecolor='w',
                           fancybox=True, framealpha=0.5, fontsize="large")
        plt.setp(legend.get_texts(), color='w')
        # set all desired settings for the image before saving
        ax.set_xlabel("river section (m)")
        ax.set_ylabel("height (m)")
        ax.set_title("Water levels on river axis")
        ax.spines['bottom'].set_color('w')
        ax.spines['top'].set_color('w') 
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('w')
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        ax.yaxis.label.set_color('w')
        ax.yaxis.label.set_fontsize(14)
        ax.xaxis.label.set_color('w')
        ax.xaxis.label.set_fontsize(14)
        ax.title.set_fontsize(20)
        ax.title.set_color('w')
        plt.tight_layout()
        plt.savefig(join(self.web_dir, "flood_safety_score1.png"),
                    edgecolor='w', transparent=True)
        return
    
    def dike_safety_graph(self):
        """
        Function to draw the dike safety overview image that is displayed in
        the flood safety indicator in Tygron.
        """
        plt.ioff()
        fig, ax = plt.subplots()
        x_min = 0
        x_max = 0
        # draw the north dike and color each segment based on difference
        # between water levels on the river axis and the dike height.
        if self.north_dike:
            for feature in self.north_dike.features:
                points = feature.geometry["coordinates"]
                x, y = zip(*points)
                for value in x:
                    if value < x_min:
                        x_min = value
                    elif value > x_max:
                        x_max = value
                if feature.properties["difference"] < self.unsafe:
                    color = 'r'
                elif feature.properties["difference"] < self.safer:
                    color = 'y'
                else:
                    color = 'g'
                ax.plot(x, y, color=color, linewidth=5.0)
        # draw the south dike and color each segment based on difference
        # between water levels on the river axis and the dike height.
        if self.south_dike:
            for feature in self.south_dike.features:
                points = feature.geometry["coordinates"]
                x, y = zip(*points)
                if feature.properties["difference"] < self.unsafe:
                    color = 'r'
                elif feature.properties["difference"] < self.safer:
                    color = 'y'
                else:
                    color = 'g'
                ax.plot(x, y, color=color, linewidth=5.0)
        # draw the main channel.
        if self.river_axis is not None:
            points = self.river_axis.geometry["coordinates"]
            x, y = zip(*points)
            ax.plot(x, y, color='b', linewidth=30.0)
        # create and add the legend
        red_patch = mpatches.Patch(color='r', label='1/500')
        yellow_patch = mpatches.Patch(color='y', label='1/1000')
        green_patch = mpatches.Patch(color='g', label='1/1250')
        
        legend = ax.legend(handles=[red_patch, yellow_patch, green_patch],
                           loc='best', facecolor='black', edgecolor='w',
                           fancybox=True, framealpha=0.5, fontsize="large")
        plt.setp(legend.get_texts(), color='w')
        # set all desired settings for the image before saving
        #ax.set_xlabel("river section x")
        #ax.set_ylabel("river section y")
        ax.set_title("Dike segment flooding chances")
        ax.spines['bottom'].set_color('w')
        ax.spines['top'].set_color('w') 
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('w')
        ax.set_xlim(x_min, x_max)
        # remove the x and y ticks including labels (we just want an overview)
        ax.tick_params(axis='both', which='both', colors='w', top=False,
                       bottom=False, left=False, right=False,
                       labelbottom=False, labeltop=False, labelleft=False,
                       labelright=False)
        ax.yaxis.label.set_color('w')
        ax.yaxis.label.set_fontsize(14)
        ax.xaxis.label.set_color('w')
        ax.xaxis.label.set_fontsize(14)
        ax.title.set_fontsize(20)
        ax.title.set_color('w')
        plt.tight_layout()
        plt.savefig(join(self.web_dir, "flood_safety_score2.png"),
                    edgecolor='w',transparent=True)
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