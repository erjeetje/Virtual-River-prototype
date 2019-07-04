# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 14:31:27 2019

@author: HaanRJ
"""

import geojson


def set_values(hexagons):
    dike_values = {"z_reference": 4,
                   "z": 4.8,
                   "landuse": 10,
                   "water": False,
                   "land": True,
                   "behind_dike": False
                   }
    floodplain_values_grass = {"z_reference": 2,
                               "z": 2.4,
                               "landuse": 2,
                               "water": False,
                               "land": True,
                               "behind_dike": False
                               }
    floodplain_values_forest = {"z_reference": 2,
                                "z": 2.4,
                                "landuse": 5,
                                "water": False,
                                "land": True,
                                "behind_dike": False
                                }
    floodplain_values_reed = {"z_reference": 2,
                              "z": 2.4,
                              "landuse": 3,
                              "water": False,
                              "land": True,
                              "behind_dike": False
                              }
    channel_values = {"z_reference": 0,
                      "z": 0,
                      "landuse": 9,
                      "water": True,
                      "land": False,
                      "behind_dike": False
                      }
    behind_dike_values = {"z_reference": 2,
                          "z": 2.4,
                          "landuse": 1,
                          "water": False,
                          "land": True,
                          "behind_dike": True
                          }
    channel_hexagons = [147, 148, 157, 158, 167, 168, 176, 177,
                        184, 185, 193, 194, 203, 204, 213, 214]
    dike_hexagons = [143, 152, 153, 161, 162, 171, 172, 180,
                     181, 189, 191, 198, 201, 207, 211, 216]
    floodplain_forest = [144, 151, 154, 160, 163, 170, 173,
                         182, 188, 192, 197, 206]
    floodplain_reed = [149, 156, 166, 195, 202, 215]
    behind_dike = [190, 199, 200, 208, 209, 210, 217, 218]
    for feature in hexagons.features:
        if not feature.properties["ghost_hexagon"]:
            continue
        else:
            if feature.id in dike_hexagons:
                values = dike_values
            elif feature.id in channel_hexagons:
                values = channel_values
            elif feature.id in floodplain_forest:
                values = floodplain_values_forest
            elif feature.id in floodplain_reed:
                values = floodplain_values_reed
            elif feature.id in behind_dike:
                values = behind_dike_values
            else:
                values = floodplain_values_grass
            feature.properties["z_reference"] = values["z_reference"]
            feature.properties["z"] = values["z"]
            feature.properties["landuse"] = values["landuse"]
            feature.properties["water"] = values["water"]
            feature.properties["land"] = values["land"]
            feature.properties["behind_dike"] = values["behind_dike"]
    if False:
        with open('ghost_cells_set_test.geojson', 'w') as f:
            geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return hexagons


def update_values(hexagons):
    for feature in hexagons.features:
        if not feature.properties["ghost_hexagon"]:
            continue
        else:
            feature.properties["z_changed"] = False
            feature.properties["landuse_changed"] = False
    return hexagons


def set_frcu(model, grid, hexagons):
    frcu = model.get_var["frcu"]
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        location = feature.properties["location"]
        hexagon = hexagons[location]
        if (hexagon.properties["z_changed"] or
            hexagon.properties["landuse_changed"]):
            feature.properties["Chezy"] = hexagon.properties["Chezy"]
            try:
                frcu[feature.id] = feature.properties["Chezy"]
            except IndexError:
                print("ERROR: It appears that the feature id is out of range of",
                      "the number of grid points.")
    