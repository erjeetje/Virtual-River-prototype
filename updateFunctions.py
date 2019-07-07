# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 09:26:52 2019

@author: HaanRJ
"""

import hexagonOwnership as owner
from geojson import FeatureCollection


def compare_hex(cost, hexagons_old, hexagons_new):
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
    costs = 0
    dike_moved = False
    for feature in hexagons_new.features:
        reference_hex = hexagons_old[feature.id]
        if feature.properties["z_reference"] != reference_hex.properties["z_reference"]:
            print("Hexagon " + str(feature.id) + " z value changed")
            feature.properties["z_changed"] = True
            z_changed.append(feature)
            if (feature.properties["z_reference"] < 2 and
                    reference_hex.properties["z_reference"] >= 2):
                becomes_water.append(feature)
            elif (feature.properties["z_reference"] >= 2 and
                    reference_hex.properties["z_reference"] < 2):
                becomes_land.append(feature)
            if (feature.properties["z_reference"] >= 4 or
                    reference_hex.properties["z_reference"] >= 4):
                print("Detected a dike relocation, will update total grid")
                dike_moved = True
        else:
            feature.properties["z_changed"] = False
        if (feature.properties["landuse"] !=
            reference_hex.properties["landuse"]):
            print("Hexagon " + str(feature.id) + " land use value changed")
            feature.properties["landuse_changed"] = True
            landuse_changed.append(feature)
        else:
            feature.properties["landuse_changed"] = False
        if (feature.properties["z_changed"] or feature.properties["landuse"]):
            z_cost, l_cost, ownership_change = cost.calc_Costs(
                    feature, reference_hex,
                    z_changed=feature.properties["z_changed"],
                    landuse_changed=feature.properties["landuse_changed"])
            feature = owner.update_ownership(feature, ownership_change)
            costs = costs + z_cost + l_cost
    return hexagons_new, costs, dike_moved


def terrain_updates(hexagons):
    """
    This function previously separated the hexagons into featurecollections
    of hexagons that should be turned into either water or land in Tygron.
    The function is no longer called as changes are handled from the feature
    properties instead.
    
    Function may be removed at a later stage.
    """
    becomes_water = []
    becomes_land = []
    for feature in hexagons.features:
        if not feature.properties["z_changed"]:
            continue
        if feature.properties["z_reference"] < 2:
            becomes_water.append(feature)
        if feature.properties["z_reference"] >= 2:
            becomes_land.append(feature)
    becomes_water = FeatureCollection(becomes_water)
    becomes_land = FeatureCollection(becomes_land)
    return becomes_water, becomes_land


if __name__ == '__main__':
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    turn = 0
    hexagons_old = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    turn += 1
    hexagons_new = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    cost = costs.Costs()
    hexagons_new, dike_moved = compare_hex(hexagons_old, hexagons_new)
    """

