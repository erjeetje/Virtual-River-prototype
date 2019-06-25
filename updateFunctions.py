# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 09:26:52 2019

@author: HaanRJ
"""

import geojson
import tygronInterface as tygron


def compare_hex(token, hexagons_old, hexagons_new):
    """
    compares the current state of each location to the previous state, should
    handle:
        - isolate changed hexagons
        - sets z_changed to True for hexagons that changed in elevation
        - sets landuse_changed to True for hexagons that changed in land use
        - sets both these properties to False if there is no change
       
    This function should also track what actually changed in order to initiate
    the cost module correctly.
    """
    z_changed = []
    becomes_water = []
    becomes_land = []
    landuse_changed = []
    dike_moved = False
    for feature in hexagons_new.features:
        reference_hex = hexagons_old[feature.id]
        if feature.properties["z"] != reference_hex.properties["z"]:
            print("hexagon " + str(feature.id) + " z value changed")
            feature.properties["z_changed"] = True
            z_changed.append(feature)
            if (feature.properties["z"] < 2 and
                    reference_hex.properties["z"] >= 2):
                becomes_water.append(feature)
            elif (feature.properties["z"] >= 2 and
                    reference_hex.properties["z"] < 2):
                becomes_land.append(feature)
            if (feature.properties["z"] >= 4 or
                    reference_hex.properties["z"] >= 4):
                print("Detected a dike relocation, will update total grid")
                dike_moved = True
        else:
            feature.properties["z_changed"] = False
        if (feature.properties["landuse"] !=
            reference_hex.properties["landuse"]):
            print("hexagon " + str(feature.id) + " land use value changed")
            feature.properties["landuse_changed"] = True
            landuse_changed.append(feature)
        else:
            feature.properties["landuse_changed"] = False
    return hexagons_new, dike_moved


def terrain_updates(hexagons):
    becomes_water = []
    becomes_land = []
    for feature in hexagons.features:
        if not feature.properties["z_changed"]:
            continue
        if feature.properties["z"] < 2:
            becomes_water.append(feature)
        if feature.properties["z"] >= 2:
            becomes_land.append(feature)
    becomes_water = geojson.FeatureCollection(becomes_water)
    becomes_land = geojson.FeatureCollection(becomes_land)
    return becomes_water, becomes_land


if __name__ == '__main__':
    with open('hexagons_tygron_update_transformed_test2.geojson') as f:
        hexagons_old = geojson.load(f)
    with open('hexagons_tygron_update_transformed_test1.geojson') as g:
        hexagons_new = geojson.load(g)
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    token = tygron.join_session(username, password)
    if token is None:
        print("logging in to Tygron failed, unable to make changes in Tygron")
    else:
        token = "token=" + token
        z = compare_hex(token, hexagons_old, hexagons_new)
