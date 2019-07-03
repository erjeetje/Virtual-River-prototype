# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 14:31:27 2019

@author: HaanRJ
"""

import geojson


def set_values(hexagons):
    dike_values = {"z": 4,
                   "landuse": 10,
                   "water": False,
                   "land": True,
                   "behind_dike": False
                   }
    floodplain_values_grass = {"z": 2,
                         "landuse": 2,
                         "water": False,
                         "land": True,
                         "behind_dike": False
                         }
    floodplain_values_forest = {"z": 2,
                         "landuse": 5,
                         "water": False,
                         "land": True,
                         "behind_dike": False
                         }
    channel_values = {"z": 0,
                      "landuse": 9,
                      "water": True,
                      "land": False,
                      "behind_dike": False
                      }
    for feature in hexagons.features:
        if not feature.properties["ghost_hexagon"]:
            continue
        else:
            if (feature.id == 143 or feature.id == 151 or
                feature.id == 152 or feature.id == 160):
                values = dike_values
            elif (feature.id == 146 or feature.id == 147 or
                  feature.id == 156 or feature.id == 157):
                values = channel_values
            elif (feature.id == 144 or feature.id == 150 or
                feature.id == 153 or feature.id == 159):
                values = floodplain_values_forest
            else:
                values = floodplain_values_grass
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
        hexagon = hexagons_by_id[location]
        if (hexagon.properties["z_changed"] or
            hexagon.properties["landuse_changed"]):
            feature.properties["Chezy"] = hexagon.properties["Chezy"]
            try:
                frcu[feature.id] = feature.properties["Chezy"]
            except IndexError:
                print("ERROR: It appears that the feature id is out of range of",
                      "the number of grid points.")
    