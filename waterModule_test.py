# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


import os
import geojson
import numpy as np
import matplotlib.pyplot as plt
import gridMapping as gridmap
import createStructures as structures
import modelInterface as model
from shapely import geometry
from copy import deepcopy
from scipy.spatial import cKDTree


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
            water_level = feature.properties["water_level"]  # - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(water_level)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    return water_level


def water_levels_new(hexagons):
    water_level_columns = [[] for i in range(15)]
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["main_channel"]:
            water_level = feature.properties["water_level"]  # - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            water_level_columns[column].append(water_level)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    print(water_level)
    return water_level


def grid_to_hex(hexagons, grid):
    for feature in hexagons.features:
        if feature.properties["crosssection"] is None:
            continue
        face_cells = feature.properties["crosssection"]
        feature.properties["water_levels"] = []
        for face_cell in face_cells:
            cell = grid.features[face_cell]
            feature.properties["water_levels"].append(cell.properties["water_level"])
    return hexagons


def water_levels_new2(hexagons):
    water_level_columns = [[] for i in range(15)]
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["main_channel"]:
            water_levels = feature.properties["water_levels"]  # - feature.properties["bedslope_correction"]
            column = feature.properties["column"] - 1
            for value in water_levels:
                water_level_columns[column].append(value)
    water_level = []
    for values in water_level_columns:
        average = round(sum(values) / len(values), 2)
        #formatted = [ '%.2f' % elem for elem in values ]
        #print("water level values:", formatted, "average:", average)
        water_level.append(average)
    print(water_level)
    return water_level


def dike_levels(hexagons):
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
    return dike_level


def bed_levels(hexagons):
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
    return bed_level


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

def plot_water_levels(xvals, yvals, label="", turn=0, fig=None, ax=None,
                      x_mani=-30):
    xvals = []
    for i in range(len(yvals)):
        xvals.append(i * x_mani + 3500)
    if fig is None:
        fig, ax = plt.subplots(1)
        ax.set_xlabel('river section (meters)')
        ax.set_ylabel('water levels (meters)')
    """
    if turn == 0:
        label = "initial board"
    else:
        label = ("board after turn " + str(turn))
    """
    ax.plot(xvals, yvals, label=label)
    ax.legend(loc='upper right')
    plt.show
    return fig, ax


def get_channel(hexagons):
    hexagons_copy = deepcopy(hexagons)
    channel = []
    for feature in hexagons_copy.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["main_channel"]:
            channel.append(feature)
    channel = geojson.FeatureCollection(channel)
    return channel


def get_crosssection(hexagons, grid, save=False):
    crosssection_coor = []
    crosssection_id = []
    crosssection_ref = []
    crosssections = []
    count = -1
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if not feature.properties["main_channel"]:
            continue
        count += 1
        shape = geometry.asShape(feature.geometry)
        x = shape.centroid.x
        y = shape.centroid.y
        line = list(geojson.utils.coords(feature.geometry))
        miny = y
        maxy = y
        for x_point, y_point in line:
            if y_point < miny:
                miny = y_point
            if y_point > maxy:
                maxy = y_point
        crosssection_coor.append([x, y])
        line = geojson.LineString([[x, miny], [x, maxy]])
        crosssection = geojson.Feature(id=feature.id, geometry=line)
        crosssections.append(crosssection)
        crosssection_id.append(count)
        crosssection_ref.append(feature.id)

    crosssections = geojson.FeatureCollection(crosssections)
    crosssection_coor = np.array(crosssection_coor)
    crosssection_tree = cKDTree(crosssection_coor)
    
    length = len(crosssection_coor)
    hex_refs = []
    face_cells = []
    for feature in grid.features:
        xy = feature.geometry["coordinates"]
        dist, index = crosssection_tree.query(xy, distance_upper_bound = 35)
        if index < length:
            crosssection = crosssections.features[crosssection_id[index]]
            shape = geometry.asShape(crosssection.geometry)
            point = geometry.asShape(feature.geometry)
            distance = point.distance(shape)
            if distance < 3:
                feature.properties["crosssection_of_hex"] = crosssection_ref[index]
                hex_refs.append(crosssection.id)
                face_cells.append(feature.id)
            else:
                feature.properties["crosssection_of_hex"] = None
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            feature.properties["crosssection"] = None
            continue
        if not feature.properties["main_channel"]:
            feature.properties["crosssection"] = None
            continue
        feature.properties["crosssection"] = []
        for i, hex_id in enumerate(hex_refs):
            if hex_id == feature.id:
                feature.properties["crosssection"].append(face_cells[i])
    if save:
        with open('crosssections.geojson', 'w') as f:
            geojson.dump(crosssections, f, sort_keys=True, indent=2)
        with open('hex_with_crosssections.geojson', 'w') as f:
            geojson.dump(hexagons, f, sort_keys=True, indent=2)
        with open('crosssections_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return hexagons


def grid_columns(grid, save=False):
    x_coor = []
    xrange_min = -400
    xrange_max = 400
    yrange_min = -300
    yrange_max = 300
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x = shape.centroid.x
        y = shape.centroid.y
        if (x < xrange_min or x > xrange_max or y < yrange_min or y > yrange_max):
            continue
        x_coor.append(x)
    x_coor = np.unique(x_coor)
    x_coor.sort()
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x = shape.centroid.x
        y = shape.centroid.y
        if (x < xrange_min or x > xrange_max or y < yrange_min or y > yrange_max):
            feature.properties["column"] = None
            continue
        x_index = np.where(x_coor == x)[0][0]
        feature.properties["column"] = int(x_index)
    if save:
        with open('columns_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def grid_river_axis(hexagons, grid, save=False):
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
    river_axis = geometry.asShape(line)
    columns_covered = []
    distances = []
    feature_ids = []
    for feature in grid.features:
        if feature.properties["column"] is None:
            continue
        point = geometry.asShape(feature.geometry)
        distance = point.distance(river_axis)
        if distance < 3:
            column = feature.properties["column"]
            if feature.properties["column"] in columns_covered:
                reference_column = columns_covered.index(column)
                reference_distance = distances[reference_column]
                if reference_distance > distance:
                    distances[reference_column] = distance
                    feature_ids[reference_column] = feature.id
            else:
                columns_covered.append(column)
                distances.append(column)
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
        with open('river_axis_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def grid_river_axis_new(hexagons, grid, save=False):
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
    river_axis = geometry.asShape(line)
    columns_covered = []
    #distances = []
    feature_ids = []
    for feature in grid.features:
        if feature.properties["column"] is None:
            continue
        point = geometry.asShape(feature.geometry)
        distance = point.distance(river_axis)
        if distance < 6:
            column = feature.properties["column"]
            columns_covered.append(column)
            #distances.append(column)
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


def grid_river_axis_water_levels(grid, model, save=False):
    #s1 = model.get_var('s1')
    x_output = []
    s1_output = []
    for feature in grid.features:
        if not feature.properties["river_axis"]:
            continue
        #s = s1[feature.id]
        s = feature.properties["water_level"]
        column = feature.properties["column"]
        x_output.append(column)
        s1_output.append(s)
    if save:
        with open('river_axis_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return x_output, s1_output


def grid_river_axis_water_levels_new(grid, save=False):
    def get_average(s1_list):
        average_list = []
        for values in s1_list:
            try:
                average = sum(values) / len(values)
                average_list.append(average)
            except ZeroDivisionError:
                continue
        return average_list
    #s1 = model.get_var('s1')
    columns = []
    model_output = [[] for i in range(134)]
    for feature in grid.features:
        if not feature.properties["river_axis"]:
            continue
        #s = s1[feature.id]
        s = feature.properties["water_level"]
        column = feature.properties["column"]
        columns.append(column)
        model_output[column].append(s)
    max_columns = max(columns)
    x_output = [i for i in range(max_columns+1)]
    s1_output = get_average(model_output)
    if save:
        with open('river_axis_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return x_output, s1_output


def grid_waterlevels(grid, model, save=False):
    s1 = model.get_var('s1')
    bl = model.get_var('bl')
    number_of_columns = 0
    columns = []
    s1_columns = []
    for feature in grid.features:
        if feature.properties["column"] is None:
            continue
        column = feature.properties["column"]
        if column > number_of_columns:
            number_of_columns = column
        z = bl[feature.id]
        if z > 13:
            continue
        s = s1[feature.id]
        columns.append(column)
        s1_columns.append(s)
        feature.properties["water_level"] = s
    columns = np.array(columns)
    s1_columns = np.array(s1_columns)
    water_levels = []
    print_columns = []
    for i in range(number_of_columns + 1):
        indexes = np.where(columns == i)[0]
        column_water_levels = s1_columns[indexes]
        average = round(sum(column_water_levels) / len(column_water_levels), 2)
        water_levels.append(average)
        print_columns.append(i)
    print("water levels in grid crosssections:")
    print(print_columns)
    print(water_levels)
    if save:
        with open('water_levels_grid.geojson', 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


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
    
    # complete crosssections
    turn = 0
    hexagons = load(turn=turn)
    face_grid = load_grid(turn=turn)
    face_grid = grid_river_axis_new(hexagons, face_grid)
    x_output, water_levels = grid_river_axis_water_levels_new(face_grid, save=True)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 0", turn=turn)
    hexagons = load(turn=1)
    face_grid = load_grid(turn=1)
    face_grid = grid_river_axis_new(hexagons, face_grid)
    x_output, water_levels = grid_river_axis_water_levels_new(face_grid)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 1", turn=turn,
                                fig=fig, ax=ax)
    hexagons = load(turn=2)
    face_grid = load_grid(turn=2)
    face_grid = grid_river_axis_new(hexagons, face_grid)
    x_output, water_levels = grid_river_axis_water_levels_new(face_grid)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 2", turn=turn,
                                fig=fig, ax=ax)
    hexagons = load(turn=3)
    face_grid = load_grid(turn=3)
    face_grid = grid_river_axis_new(hexagons, face_grid)
    x_output, water_levels = grid_river_axis_water_levels_new(face_grid)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 3", turn=turn,
                                fig=fig, ax=ax)
    hexagons = load(turn=4)
    face_grid = load_grid(turn=4)
    face_grid = grid_river_axis_new(hexagons, face_grid)
    x_output, water_levels = grid_river_axis_water_levels_new(face_grid)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 4", turn=turn,
                                fig=fig, ax=ax)
    dike_level = dike_levels(hexagons)
    x_output = get_river_length(water_levels)
    fig, ax = plot_water_levels(x_output, dike_level,
                                label="dike level", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    """
    # channel hexagons crosssections
    turn = 0
    hexagons = load(turn=turn)
    #D3D = model.Model()
    face_grid = load_grid(turn=turn)
    hexagons = grid_to_hex(hexagons, face_grid)
    water_levels = water_levels_new2(hexagons)
    x_output = get_river_length(water_levels)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 0", turn=turn,
                                x_mani=-250)
    hexagons = load(turn=1)
    face_grid = load_grid(turn=1)
    hexagons = grid_to_hex(hexagons, face_grid)
    water_levels = water_levels_new2(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 1", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=2)
    face_grid = load_grid(turn=2)
    hexagons = grid_to_hex(hexagons, face_grid)
    water_levels = water_levels_new2(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 2", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=3)
    face_grid = load_grid(turn=3)
    hexagons = grid_to_hex(hexagons, face_grid)
    water_levels = water_levels_new2(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 3", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=4)
    face_grid = load_grid(turn=4)
    hexagons = grid_to_hex(hexagons, face_grid)
    water_levels = water_levels_new2(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 4", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    dike_level = dike_levels(hexagons)
    fig, ax = plot_water_levels(x_output, dike_level,
                                label="dike level", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    """
    
    """
    # average of main channel hexagons
    turn = 0
    hexagons = load(turn=turn)
    #D3D = model.Model()
    #face_grid = load_grid(turn=turn)
    water_levels = water_levels_new(hexagons)
    x_output = get_river_length(water_levels)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 0", turn=turn,
                                x_mani=-250)
    hexagons = load(turn=1)
    water_levels = water_levels_new(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 1", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=2)
    water_levels = water_levels_new(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 2", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=3)
    water_levels = water_levels_new(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 3", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    hexagons = load(turn=4)
    water_levels = water_levels_new(hexagons)
    fig, ax = plot_water_levels(x_output, water_levels,
                                label="water levels turn 4", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    dike_level = dike_levels(hexagons)
    fig, ax = plot_water_levels(x_output, dike_level,
                                label="dike level", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    """
    
    """
    # river axis in grid
    turn = 0
    hexagons = load(turn=turn)
    D3D = model.Model()
    face_grid = load_grid(turn=turn)
    #face_grid = grid_columns(face_grid, save=True)
    #face_grid = grid_waterlevels(face_grid, D3D.model)
    #water_model = D3D.initialize_model()
    #channel = get_channel(hexagons)
    #hexagons = get_crosssection(hexagons, face_grid, save=False)
    #face_grid = grid_river_axis(hexagons, face_grid, save=False)
    x_output, water_level = grid_river_axis_water_levels(face_grid, D3D.model)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels turn 0", turn=turn)
    face_grid = load_grid(turn=1)
    x_output, water_level = grid_river_axis_water_levels(face_grid, D3D.model)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels turn 1", turn=turn,
                                fig=fig, ax=ax)
    face_grid = load_grid(turn=2)
    x_output, water_level = grid_river_axis_water_levels(face_grid, D3D.model)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels turn 2", turn=turn,
                                fig=fig, ax=ax)
    face_grid = load_grid(turn=3)
    x_output, water_level = grid_river_axis_water_levels(face_grid, D3D.model)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels turn 3", turn=turn,
                                fig=fig, ax=ax)
    face_grid = load_grid(turn=4)
    x_output, water_level = grid_river_axis_water_levels(face_grid, D3D.model)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels turn 4", turn=turn,
                                fig=fig, ax=ax)
    dike_level = dike_levels(hexagons)
    x_output = get_river_length(water_level)
    fig, ax = plot_water_levels(x_output, dike_level,
                                label="dike level", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    bed_level = bed_levels(hexagons)
    fig, ax = plot_water_levels(x_output, bed_level,
                                label="river bed level", turn=turn,
                                fig=fig, ax=ax, x_mani=-250)
    #water_level = water_levels(hexagons)
    #water_level = water_levels_new(hexagons)
    """
    """
    water_level = water_levels_new2(hexagons)
    dike_level = dike_levels(hexagons)
    x_output = get_river_length(water_level)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels crosssections", turn=turn)
    fig, ax = plot_water_levels(x_output, dike_level,
                                label="dike levels", turn=turn,
                                fig=fig, ax=ax)
    water_level = water_levels_new(hexagons)
    fig, ax = plot_water_levels(x_output, water_level,
                                label="water levels old", turn=turn, fig=fig,
                                ax=ax)
    """
    #dike_levels = [5 for i in range(0, 15)]
    #water_levels = [4 for i in range (0, 15)]
    #flood_safety_levels = flood_safety(dike_levels, water_levels)
    return

if __name__ == '__main__':
    main()