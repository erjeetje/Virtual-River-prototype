# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 06:37:58 2019

@author: HaanRJ
"""

import os
import random
import geojson
import numpy as np
import gridMapping as gridmap
from cv2 import fillPoly
from scipy.spatial import cKDTree
from shapely import geometry


def determine_neighbours(hexagons):
    """
    Function that indexes all hexagons to their neighbours. Finds all hexagons
    that are direct neighbours of each hexagon and stores their value in the
    hexagon properties.
    """
    def remove_values_from_array(array, val):
        return [value for value in array if value <= val]

    hex_coor = []
    polygons = []
    hexagon0_y = 0
    hexagon1_y = 0
    hexagon_count = 0
    for feature in hexagons.features:
        if not feature.properties["ghost_hexagon"]:
            hexagon_count += 1
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        if feature.id == 0:
            hexagon0_y = y_hex
        if feature.id == 1:
            hexagon1_y = y_hex
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    limit = abs((hexagon0_y - hexagon1_y) * 1.5)
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        # find all hexagons within the limit radius
        dist, indices = hex_locations.query(
                xy, k=7, distance_upper_bound=limit)
        # remove missing neighbours (return as self.n, equal to total_hex)
        indices = remove_values_from_array(indices, hexagon_count)
        # convert from int32 to regular int (otherwise JSON error)
        indices = list(map(int, indices))
        # remove itself
        indices.pop(0)
        print("Neighbouring hexagons for hexagon " + str(feature.id) +
              " are: " + str(indices))
        feature.properties["neighbours"] = indices
    return hexagons


def determine_ownership(hexagons):
    """
    Function that generates random ownership based on:
        - Overall size of initial floodplain area
        - Landuse state of hexagons
    Function generates random seeds and looks at neighbouring hexagons. Assigns
    areas of size 2 to 3 hexagons that are within the floodplains to the
    players. Skips landuses 0 (buildings) and 1 (agriculture). These hexagons
    are initially not assigned to any player.
    """
    def floodplain_count(hexagons, side="north"):
        count = 0
        indices = []
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if side == "south":
                if feature.properties["floodplain_south"]:
                    count += 1
                    indices.append(feature.id)
            else:
                if feature.properties["floodplain_north"]:
                    count += 1
                    indices.append(feature.id)
        return indices, count

    def check_floodplain(floodplain_indices, neighbours):
        is_floodplain = []
        for index in neighbours:
            if index in floodplain_indices:
                is_floodplain.append(index)
        return is_floodplain

    north_indices, north_count = floodplain_count(hexagons, side="north")
    south_indices, south_count = floodplain_count(hexagons, side="south")
    floodplain_count = north_count + south_count
    floodplain_indices = north_indices + south_indices
    if floodplain_count < 55:
        nature_count = 4
        water_count = 2
        province_count = 2
    elif floodplain_count < 65:
        nature_count = 5
        water_count = 2
        province_count = 3
    else:
        nature_count = 6
        water_count = 3
        province_count = 3
    total_count = nature_count + water_count + province_count
    taken_hexagons = []
    #for i in range(0, nature_count):
    i = 0
    while i < total_count:
        #print(taken_hexagons)
        #print("Trial loop nature ownership: " + str(i))
        random_value = random.randint(0, floodplain_count-1)
        if random_value in taken_hexagons:
            #i += -1
            continue
        else:
            taken_hexagons.append(random_value)
        random_hexagon = floodplain_indices[random_value]
        print("")
        print("Trying from hexagon: " + str(random_hexagon))
        hexagon = hexagons[random_hexagon]
        if hexagon.properties["owned"]:
            continue
        if (hexagon.properties["landuse"] == 0 or
            hexagon.properties["landuse"] == 1):
            continue
        neighbours = hexagon.properties["neighbours"]
        print("Neighbours are: " + str(neighbours))
        floodplain_neighbours = check_floodplain(
                floodplain_indices, neighbours)
        print("Floodplain neighbours are: " + str(floodplain_neighbours))
        if i < nature_count:
            owner = "Nature"
        elif i < (nature_count + water_count):
            owner = "Water"
        else:
            owner = "Province"
        if not floodplain_neighbours:
            continue
        elif len(floodplain_neighbours) == 1:
            chosen_neighbour = floodplain_neighbours[0]
            if chosen_neighbour in taken_hexagons:
                continue
            neighbour_hexagon = hexagons[chosen_neighbour]
            if neighbour_hexagon.properties["owned"]:
                continue
            if (neighbour_hexagon.properties["landuse"] == 0 or
                neighbour_hexagon.properties["landuse"] == 1):
                continue
            else:
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = owner
                neighbour_hexagon.properties["owned"] = True
                neighbour_hexagon.properties["owner"] = owner
                i += 1
                taken_hexagons.append(chosen_neighbour)
                print(owner + " ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbour))
                continue
        else:
            if len(floodplain_neighbours) == 2:
                chosen_neighbours = floodplain_neighbours
            else:
                random_neighbours = random.sample(floodplain_neighbours, 2)
                chosen_neighbours = random_neighbours
            if (chosen_neighbours[0] in taken_hexagons and
                chosen_neighbours[1] in taken_hexagons):
                continue
            neighbour_hexagon1 = hexagons[chosen_neighbours[0]]
            neighbour_hexagon2 = hexagons[chosen_neighbours[1]]
            if (neighbour_hexagon1.properties["owned"] and
                neighbour_hexagon2.properties["owned"]):
                continue
            if ((neighbour_hexagon1.properties["landuse"] == 0 or
                neighbour_hexagon1.properties["landuse"] == 1) and
                (neighbour_hexagon2.properties["landuse"] == 0 or
                neighbour_hexagon2.properties["landuse"] == 1)):
                continue
            if (neighbour_hexagon1.properties["owned"] or 
                neighbour_hexagon1.properties["landuse"] == 0 or
                neighbour_hexagon1.properties["landuse"] == 1):
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = owner
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = owner
                i += 1
                taken_hexagons.append(chosen_neighbours[1])
                print(owner + " ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[1]))
            elif (neighbour_hexagon2.properties["owned"] or
                  neighbour_hexagon2.properties["landuse"] == 0 or
                  neighbour_hexagon2.properties["landuse"] == 1):
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = owner
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = owner
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                print(owner + " ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]))
            else:
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = owner
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = owner
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = owner
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                taken_hexagons.append(chosen_neighbours[1])
                print(owner + " ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]) + ", " +
                      str(chosen_neighbours[1]))
    return hexagons


def generate_ownership(hexagons):
    for feature in hexagons.features:
        feature.properties["owned"] = False
        feature.properties["owner"] = None
        feature.properties["ownership_change"] = False
    return hexagons


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
        pts = pts + [400, 300]
        pts = pts * [0.75, 0.75]
        pts = pts.astype(np.int32)

        # draw the hexagon as a filled polygon
        fillPoly(img, pts, color)
    return img


def update_ownership(feature, ownership_change):
    if ownership_change is not None:
        feature.properties["ownership_change"] = True
        feature.properties["owner"] = ownership_change
    else:
        feature.properties["ownership_change"] = False
    return feature


def main():
    turn=0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'storing_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    hexagons = determine_neighbours(hexagons)
    hexagons = generate_ownership(hexagons)
    hexagons = determine_ownership(hexagons)
    with open(os.path.join(test_path, 'hexagons%d.geojson' % turn),
              'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
