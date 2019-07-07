# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 06:37:58 2019

@author: HaanRJ
"""

import random
import geojson
import numpy as np
from scipy.spatial import cKDTree
from shapely import geometry
from shapely.ops import unary_union
import gridMapping as gridmap


"""
To do:
    - get the number of floodplain hexagon cells
    - declare owners (water, nature, <third>)
    - establish number of hexagons per player
    - generate patches of size 3 to 5
    - update hexagon properties
"""


def determine_neighbours(hexagons):
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


def remove_values_from_array(array, val):
    return [value for value in array if value <= val]


def determine_ownership(hexagons):
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
    north_indices, north_count = floodplain_count(hexagons, side="north")
    south_indices, south_count = floodplain_count(hexagons, side="south")
    floodplain_count = north_count + south_count
    floodplain_indices = north_indices + south_indices
    if floodplain_count < 55:
        nature_count = 4
        water_count = 2
        province_count = 2
    elif floodplain_count < 70:
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
    """
    i = 0
    print("")
    print("WATER OWNERSHIP")
    print("")
    while i < water_count:
        #print(taken_hexagons)
        #print("Trial loop water ownership: " + str(i))
        random_value = random.randint(0, floodplain_count-1)
        if random_value in taken_hexagons:
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
                hexagon.properties["owner"] = "Water"
                neighbour_hexagon.properties["owned"] = True
                neighbour_hexagon.properties["owner"] = "Water"
                i += 1
                taken_hexagons.append(chosen_neighbour)
                print("Water ownership of hexagons: " + str(random_hexagon) +
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
                hexagon.properties["owner"] = "Water"
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = "Water"
                i += 1
                taken_hexagons.append(chosen_neighbours[1])
                print("Water ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[1]))
            elif (neighbour_hexagon2.properties["owned"] or
                  neighbour_hexagon2.properties["landuse"] == 0 or
                  neighbour_hexagon2.properties["landuse"] == 1):
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = "Water"
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = "Water"
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                print("Water ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]))
            else:
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = "Water"
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = "Water"
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = "Water"
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                taken_hexagons.append(chosen_neighbours[1])
                print("Water ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]) + ", " +
                      str(chosen_neighbours[1]))
    i = 0
    print("")
    print("PROVINCE OWNERSHIP")
    print("")
    while i < province_count:
        #print(taken_hexagons)
        #print("Trial loop province ownership: " + str(i))
        random_value = random.randint(0, floodplain_count-1)
        if random_value in taken_hexagons:
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
        if not floodplain_neighbours:
            continue
        elif len(floodplain_neighbours) == 1:
            chosen_neighbour = floodplain_neighbours[0]
            neighbour_hexagon = hexagons[chosen_neighbour]
            if neighbour_hexagon.properties["owned"]:
                continue
            if (neighbour_hexagon.properties["landuse"] == 0 or
                neighbour_hexagon.properties["landuse"] == 1):
                continue
            else:
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = "Province"
                neighbour_hexagon.properties["owned"] = True
                neighbour_hexagon.properties["owner"] = "Province"
                i += 1
                taken_hexagons.append(chosen_neighbour)
                print("Province ownership of hexagons: " + str(random_hexagon) +
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
                hexagon.properties["owner"] = "Province"
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = "Province"
                i += 1
                taken_hexagons.append(chosen_neighbours[1])
                print("Province ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[1]))
            elif (neighbour_hexagon2.properties["owned"] or
                  neighbour_hexagon2.properties["landuse"] == 0 or
                  neighbour_hexagon2.properties["landuse"] == 1):
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = "Province"
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = "Province"
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                print("Province ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]))
            else:
                hexagon.properties["owned"] = True
                hexagon.properties["owner"] = "Province"
                neighbour_hexagon1.properties["owned"] = True
                neighbour_hexagon1.properties["owner"] = "Province"
                neighbour_hexagon2.properties["owned"] = True
                neighbour_hexagon2.properties["owner"] = "Province"
                i += 1
                taken_hexagons.append(chosen_neighbours[0])
                taken_hexagons.append(chosen_neighbours[1])
                print("Province ownership of hexagons: " + str(random_hexagon) +
                      ", " + str(chosen_neighbours[0]) + ", " +
                      str(chosen_neighbours[1]))
    """
    return hexagons


def check_floodplain(floodplain_indices, neighbours):
    is_floodplain = []
    for index in neighbours:
        if index in floodplain_indices:
            is_floodplain.append(index)
    return is_floodplain
    


def generate_ownership(hexagons):
    for feature in hexagons.features:
        feature.properties["owned"] = False
        feature.properties["owner"] = None
    return hexagons


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

"""
def owners(hexagons):
    count = 0
    for feature in hexagons.features:
        if feature.properties["floodplain"]:
            count += 1
    print("number of floodplain cells: ")
    return hexagons


def determine_ownership(hexagons):
    owner = ["red", "green" ,"blue"]
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            continue
        count += 1
    ownership = random.choices(owner, k=count)
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["owner"] = None
        else:
            feature.properties["owner"] = ownership[count]
            count += 1
    with open('ownership_test.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return hexagons



def determine_ownership4(hexagons):
    owner = ["red", "green" ,"blue"]
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            continue
        count += 1
    ownership = random.choices(owner, k=count)
    count = 0
    for feature in hexagons.features:
        if (feature.properties["north_dike"] or
            feature.properties["south_dike"] or
            feature.properties["main_channel"] or
            feature.properties["behind_dike"]):
            feature.properties["owner"] = None
        else:
            feature.properties["owner"] = ownership[count]
            count += 1
    with open('ownership_test.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return hexagons


def determine_ownership2(hexagons):
    hex_coor = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    count = 0
    owner = random.randint(1, 3)
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        dist, index = hex_locations.query(xy, k=7)
    return hexagons


def determine_ownership3():
    ownership = []
    ownership = add_ownership(ownership)
    while len(ownership) < 100:
        ownership = add_ownership(ownership)
    print(ownership)
    return


def add_ownership(ownership):
    length = random.randint(3, 5)
    owner = random.randint(1, 3)
    print(length)
    for i in range(0, length):
        print(owner)
        ownership.append(owner)
    return ownership
"""
"""
Separate north and south floodplains ? ==>
Create empty list of ownership ==>
Create random len(3-5) list of 

Generate (semi) random points within the board ==> cKDTree ==> index hexagons
to random points ==> assign ownership
"""
"""
def random_points(hexagons):
    polygons = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        polygons.append(shape)
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    line = list(geojson.utils.coords(board_feature))

    # determine the bounding box coordinates of the board.
    minx = 0.0
    miny = 0.0
    maxx = 0.0
    maxy = 0.0
    for x, y in line:
        if x < minx:
            minx = x
        elif x > maxx:
            maxx = x
        if y < miny:
            miny = y
        elif y > maxy:
            maxy = y
    x_clusters = 6
    y_clusters = 4
    x_step = (abs(minx) + maxx) / x_clusters
    y_step = (abs(miny) + maxy) / y_clusters
    random_points = []
    ownership_points = []
    seed_length = x_clusters * y_clusters
    owner = ["red", "green" ,"blue"]
    ownership = random.choices(owner, k=seed_length)
    i = 0
    for a in range(0, x_clusters):  # range reflects gridsize in x direction
        for b in range(0, y_clusters):  # range reflects gridsize in y direction
            x = (x_step * random.random()) + (x_step * a) - abs(minx)
            y = (y_step * random.random()) + (y_step * b) - abs(miny)
            xy = [round(x), round(y)]
            random_points.append(xy)
            point = geojson.Point(xy)
            feature = geojson.Feature(id=i, geometry=point)
            feature.properties["owner"] = ownership[i]
            ownership_points.append(feature)
            i += 1
    random_points = np.array(random_points)
    points_locations = cKDTree(random_points)
    ownership_points = geojson.FeatureCollection(ownership_points)
    #points_by_id = {feature.id: feature for feature in ownership_points.features}
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        dist, index = points_locations.query(xy)
        feature.properties["ownership_index"] = index
        point = ownership_points[index]
        feature.properties["owner"] = point.properties["owner"]
        print("ownership for hexagon " + str(feature.id) + ": " +
              str(feature.properties["owner"]))
    return hexagons
"""

if __name__ == '__main__':
    with open('storing_files\\hexagons0.geojson', 'r') as f:
        hexagons = geojson.load(f)
    """
    hexagons = gridmap.hexagons_to_fill(hexagons)
    hexagons = determine_ownership(hexagons)
    """
    hexagons = determine_neighbours(hexagons)
    hexagons = generate_ownership(hexagons)
    hexagons = determine_ownership(hexagons)
    """
    count = floodplain_count(hexagons, side="north")
    print("north floodplain count: " + str(count))
    count = floodplain_count(hexagons, side="south")
    print("south floodplain count: " + str(count))
    """
    #hexagons = random_points(hexagons)
    with open('floodplain_test4.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
