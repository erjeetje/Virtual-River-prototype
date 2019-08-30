# -*- coding: utf-8 -*-
"""
Created on Fri Aug 30 10:16:51 2019

@author: HaanRJ
"""


import os
import geojson
import random
import numpy as np


def load_board(path, filename):
    with open(os.path.join(path, filename)) as f:
        features = geojson.load(f)
    return features


def save_board(hexagons, path, name):
    with open(os.path.join(path, name), 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return


def all_agriculture(hexagons):
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["floodplain_north"]:
            continue_bool = True
        elif feature.properties["floodplain_south"]:
            continue_bool = True
        else:
            continue_bool = False
        if not continue_bool:
            continue
        if feature.properties["landuse"] == 0:
            continue
        else:
            feature.properties["landuse"] = 1
        if feature.properties["z_reference"] == 1:
            feature.properties["z_reference"] = 2
    return hexagons


def all_nature(hexagons):
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if feature.properties["floodplain_north"]:
            continue_bool = True
        elif feature.properties["floodplain_south"]:
            continue_bool = True
        else:
            continue_bool = False
        if not continue_bool:
            continue
        if feature.properties["landuse"] < 7:
            random_value = random.randint(2, 5)
            feature.properties["landuse"] = random_value
        """
        if (feature.properties["z_reference"] > 1 and
            feature.properties["z_reference"] < 4):
            random_value = random.randint(1, 8)
            if random_value == 8:
                feature.properties["z_reference"] = 3
            else:
                feature.properties["z_reference"] = 2
        """
        if feature.properties["z_reference"] == 3:
            feature.properties["z_reference"] = 2
        if feature.properties["z_reference"] == 1:
            feature.properties["landuse"] = 7
    return hexagons


def create_settings():
    return


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    balance_path = os.path.join(dir_path, 'balance_tests')
    try:
        os.mkdir(balance_path)
        print("Directory ", balance_path, " Created.")
    except FileExistsError:
        print("Directory ", balance_path,
              " already exists, overwriting files.")
    filename = "hexagons0.geojson"
    hexagons = load_board(test_path, filename)
    hexagons = all_agriculture(hexagons)
    filename = "all_agriculture.geojson"
    save_board(hexagons, balance_path, filename)
    
    for i in range(0, 10):
        hexagons = all_nature(hexagons)
        filename = "all_nature%d.geojson" % i
        save_board(hexagons, balance_path, filename)


if __name__ == '__main__':
    main()