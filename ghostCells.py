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
    floodplain_values_reed = {"z": 2,
                         "landuse": 3,
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
    behind_dike_values = {"z": 2,
                      "landuse": 1,
                      "water": False,
                      "land": True,
                      "behind_dike": True
                      }
    for feature in hexagons.features:
        if not feature.properties["ghost_hexagon"]:
            continue
        else:
            if (feature.id == 143 or feature.id == 152 or
                feature.id == 153 or feature.id == 161 or
                feature.id == 162 or feature.id == 170 or
                feature.id == 172 or feature.id == 179):
                values = dike_values
            elif (feature.id == 147 or feature.id == 148 or
                  feature.id == 156 or feature.id == 157 or
                  feature.id == 166 or feature.id == 167 or
                  feature.id == 175 or feature.id == 176):
                values = channel_values
            elif (feature.id == 144 or feature.id == 151 or
                  feature.id == 154 or feature.id == 160 or
                  feature.id == 163 or feature.id == 169 or
                  feature.id == 173 or feature.id == 178):
                values = floodplain_values_forest
            elif (feature.id == 165 or feature.id == 174 or
                  feature.id == 177):
                values = floodplain_values_reed
            elif (feature.id == 171 or feature.id == 180):
                values = behind_dike_values
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
    