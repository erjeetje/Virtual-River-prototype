# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:05:07 2019

@author: HaanRJ
"""


import os
import geojson
import gridMapping as gridmap
import hexagonAdjustments as adjust


def update(turn):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    store_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=store_path)
    hexagons = adjust.biosafe_area(hexagons)
    hexagons = gridmap.hexagons_to_fill(hexagons)
    """
    hexagons_old = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    turn += 1
    hexagons_new = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    for feature in hexagons_new.features:
        reference_hex = hexagons_old[feature.id]
        feature.properties["behind_dike"] = reference_hex.properties["behind_dike"]
        feature.properties["dike_reference"] = reference_hex.properties["dike_reference"]
        feature.properties["floodplain_north"] = reference_hex.properties["floodplain_north"]
        feature.properties["floodplain_south"] = reference_hex.properties["floodplain_south"]
    print("done turn: " + str(turn))
    with open(os.path.join(test_path, 'hexagons%d.geojson' % turn), 'w') as f:
        geojson.dump(hexagons_new, f, sort_keys=True, indent=2)
    """
    with open(os.path.join(store_path, 'hexagons%d.geojson' % turn), 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return


def main():
    for i in range(0, 9):
        update(i)


if __name__ == '__main__':
    main()