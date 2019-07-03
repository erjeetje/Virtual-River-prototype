# -*- coding: utf-8 -*-
"""
Created on Tue May 21 14:23:49 2019

@author: HaanRJ
"""

import geojson
import random
import numpy as np
import gridMapping as gridmap
import modelInterface as D3D


def hex_to_points(model, hexagons, grid, test=False):
    """
    Function that sets the Chezy value of all the grid points (centers of
    cells) based on the Chezy value of the hexagon where these are located.
    
    NOTE: frcu is much longer then expected (len 52k whereas 26k was expected),
    meaning the slicing is not correct. Needs to be checked and updated.
    """
    frcu = model.get_var('frcu')
    if test:
        hexagons = randomizer(hexagons)
    hexagons = landuse_to_friction(hexagons)
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    for feature in grid.features:
        if feature.properties["fill"]:
            continue
        location = feature.properties["location"]
        hexagon = hexagons_by_id[location]
        feature.properties["Chezy"] = hexagon.properties["Chezy"]
        try:
            frcu[feature.id] = feature.properties["Chezy"]
        except IndexError:
            print("ERROR: It appears that the feature id is out of range of",
                  "the number of grid points.")
    return hexagons, grid


def randomizer(hexagons):
    """
    temporary randomize function to add different trachytopes to the board for
    testing purposes. Remove at a later stage.
    
    the function is no longer called, can be removed.
    """
    for feature in hexagons.features:
        if feature.properties["landuse"] == 9:
            continue
        elif feature.properties["z"] >= 4:
            feature.properties["landuse"] = 10
        else:
            feature.properties["landuse"] = random.randint(1, 5)
    return hexagons


def update_Chezy_values(hexagons, filled_hexagons):
    for feature in hexagons.features:
        reference_hex = filled_hexagons[feature.id]
        feature.properties["Chezy"] = reference_hex.properties["Chezy"]
    return hexagons


def landuse_to_friction(hexagons, printing=False):
    """
    Function that turns the landuse into a trachytope.
    
    landuse range between 0 and 9, with a subdivision for 0:
    0: built environment
    1: agriculture; production meadow/crop field
    2: natural grassland
    3: reed; 'ruigte'
    4: shrubs; hard-/softwood
    5: forest; hard-/softwood
    6: mixtype class; mix between grass/reed/shrubs/forest
    7: water body; sidechannel (connected to main channel) or lake
    8: main channel; river bed with longitudinal training dams
    9: main channel; river bed with groynes
    10: dike
    """
    if printing:
        # the test_list is only added to print the Chezy calculations, set
        # to False by default.
        test_list = []
    for feature in hexagons.features:
        # this would require water height to be stored per hexagon    
        """
        try:
            water_level = feature.properties["water_level"]
        except KeyError:
            water_level = 6
        try:
            if feature.properties["behind_dike"]:
                dike = hexagons[feature.properties["dike_reference"]]
                z = dike.properties["z"] * 1.5
            else:
                z = feature.properties["z"] * 1.5
        except KeyError:
            try:
                z = feature.properties["z"] * 1.5
            except KeyError:
                z = 3
        h = water_level - z
        """
        try:
            h = feature.properties["water_level"] - (feature.properties["z"] * 1.5)
        except KeyError:
            try:
                h = 6 - (feature.properties["z"] * 1.5)
            except KeyError:
                h = 6    
        if h < 0:
            h = 0.0001
        if feature.properties["landuse"] == 0:
            # build environment
            vegpar = {"hv": 0.1, "n": 12, "Cd": 1.8, "kb": 0.1}  # TO DO
            handler = "building"
            name = "building          "
        elif feature.properties["landuse"] == 1:
            # agricultural land / production meadow?
            vegpar = {"hv": 0.06, "n": 45, "Cd": 1.8, "kb": 0.1}
            handler = "vegetation"
            name = "production meadow "
        elif feature.properties["landuse"] == 2:
            # grass / natural grassland
            vegpar = {"hv": 0.1, "n": 12, "Cd": 1.8, "kb": 0.1}
            handler = "vegetation"
            name = "natural grassland "
        elif feature.properties["landuse"] == 3:
            # reed and roughness / rietruigte
            vegpar = {"hv": 2, "n": 0.16, "Cd": 1.8, "kb": 0.1}
            handler = "vegetation"
            name = "reed roughness    "
        elif feature.properties["landuse"] == 4:
            # shrubs / zachthoutstruweel
            vegpar = {"hv": 6, "n": 0.13, "Cd": 1.5, "kb": 0.4}
            handler = "vegetation"
            name = "soft wood shrubs  "
        elif feature.properties["landuse"] == 5:
            # forest / zachthoutooibos
            vegpar = {"hv": 10, "n": 0.028, "Cd": 1.5, "kb": 0.6}
            handler = "vegetation"
            name = "soft wood forest  "
        elif feature.properties["landuse"] == 6:
            # mixtype
            vegpar = {"hv": 0.1, "n": 12, "Cd": 1.8, "kb": 0.1}  # TO DO
            handler = "vegetation"
            name = "vegetation mixtype"
        elif feature.properties["landuse"] == 7:
            # side channel
            n = 0.025  # check approach with Koen
            handler = "bed"
            name = "side channel      "
        elif (feature.properties["landuse"] == 8 or feature.properties["landuse"] == 9):
            # main channel
            n = 0.025  # check approach with Koen
            handler = "bed"
            name = "main channel      "
        else:
            # dike / production meadow
            vegpar = {"hv": 0.06, "n": 45, "Cd": 1.8, "kb": 0.1}
            handler = "vegetation"
            name = "dike              "
        if handler == "vegetation":
            if h <= 0:
                h = 0.1
            feature.properties["Chezy"] = klopstra(h, vegpar)
        elif handler == "bed":
            feature.properties["Chezy"] = manning(h, n)
        else:
            """
            This else statement should handle buildings --> perhaps need to
            add buildings as a geometry or structure in the model? Use manning
            for the polygon?
            """
            feature.properties["Chezy"] = klopstra(h, vegpar)
        print("Chezy coefficient calculation for cell: " +
              str(feature.id) + ". landuse: " +
              str(feature.properties["landuse"]) + ". h: " +
              str(round(h,3)) + ". C: " +
              str(round(feature.properties["Chezy"], 3)))
        if printing:
            # the test_list is only added to print the Chezy calculations,
            # set to False by default.
            test_list.append([name, h, feature.properties["Chezy"]])
    if printing:
        # the test_list is only added to print the Chezy calculations, set
        # to False by default.
        test_list = np.array(test_list)
        test_list = np.unique(test_list, axis=0)
        for item in test_list:
            print("trachytope: " + str(item[0]) + "     waterheight: "
                  + str(item[1]) + " m     Chezy: " + str(item[2]))
    return hexagons


def klopstra(h, vegpar):
    """
    Formula of Klopstra (1997), as implemented in Delft3D.
    
    Implementation should be correct (checked), but would be good to check
    again, perhaps with Hermjan.
    """
    g = 9.81
    kappa = 0.4
    if h > vegpar["hv"]:
        # ----------------------------------
        # Support terms
        # ----------------------------------

        # 'Second' implementation (1997)
        alpha = 0.0227 * vegpar["hv"] ** (0.7)

        # (squared) flow velocity vegetation
        Cb = 18 * np.log10(12 * h / vegpar["kb"])
        uvsq = vegpar["hv"] / (vegpar["Cd"] * vegpar["hv"] * vegpar["n"] /
                            2 * g + Cb ** 2)

        # (First implementation)
        #uvsq = 2 * g / (vegpar["Cd"] * vegpar.m * vegpar.D)
        uv = np.sqrt(uvsq)

        # Other support terms
        A = vegpar["n"] * vegpar["Cd"] / (2 * alpha)
        #A = vegpar.m * vegpar.D * vegpar["Cd"] / (2 * alpha)
        A2 = np.sqrt(2 * A)
        C3 = 2 * g * (h - vegpar["hv"]) / \
            (alpha * A2 * (np.exp(vegpar["hv"] * A2) +
                           np.exp(-vegpar["hv"] * A2)))

        # Distance between top of vegetation and virtual bed of surface
        # layer
        E = A2 * C3 * np.exp(vegpar["hv"] * A2) / \
            (2 * np.sqrt(C3 * np.exp(vegpar["hv"] * A2)) + uvsq)
        hs = g * (1 + np.sqrt(1 + 4 * E ** 2 * kappa ** 2 *
                              (h - vegpar["hv"]) / g)) /\
                 (2 * E ** 2 * kappa ** 2)

        # Length scale for bed roughness of the surface layer
        F = kappa * np.sqrt(C3 * np.exp(vegpar["hv"] * A2) + uvsq) / \
            np.sqrt(g * (h - (vegpar["hv"] - hs)))
        z0 = hs * np.exp(-F)

        # ----------------------------------
        # Klopstra's equation
        # ----------------------------------
        T1 = 2 / A2 * (np.sqrt(C3 * np.exp(vegpar["hv"] * A2) + uvsq))
        T2 = uvsq / A2 * \
            np.log((np.sqrt(C3 * np.exp(vegpar["hv"] * A2) + uvsq) - uv) *
                   (np.sqrt(C3 + uvsq) + uv) /
                   ((np.sqrt(C3 * np.exp(2 * A2) + uvsq) + uv) *
                    (np.sqrt(C3 + uvsq) - uv)))
        T3 = np.sqrt(g * (h - (vegpar["hv"] - hs))) / kappa * \
            ((h - (vegpar["hv"] - hs)) *
             np.log((h - (vegpar["hv"] - hs)) / z0) -
             (hs * np.log(hs / z0)) -
             (h - vegpar["hv"]))

        Chezy = (h ** (-3 / 2.)) * (T1 + T2 + T3)
    else:
        """ Emergent vegetation """
        Cb = 18 * np.log10(12 * h / vegpar["kb"])
        Chezy = np.sqrt((vegpar["Cd"] * vegpar["n"] * h / (2 * g) +
                         Cb ** -2) ** -1)
    return Chezy


def manning(h, n):
    """
    Manning formula.
    """
    Chezy = (h ** (1 / 6)) / n
    return Chezy


if __name__ == '__main__':
    hexagons = gridmap.read_hexagons(filename='storing_files\\hexagons0.geojson')
    model = D3D.initialize_model()
    face_grid = gridmap.read_face_grid(model)
    face_grid = gridmap.index_face_grid(hexagons, face_grid)
    hexagons, face_grid = hex_to_points(model, hexagons, face_grid)
    with open('hexagons_vegetation.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True,
                     indent=2)
    with open('face_grid_vegetation.geojson', 'w') as f:
        geojson.dump(face_grid, f, sort_keys=True, indent=2)
    #gridmap.run_model(grid)
