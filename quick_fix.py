# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 14:51:44 2019

@author: HaanRJ
"""

import os
import geojson
import gridMapping as gridmap
import hexagonOwnership as owner


def fix(hexagons_ownership, path, turn=0):
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=path)
    for feature in hexagons.features:
        reference_hex = hexagons_ownership[feature.id]
        """
        feature.properties["owned"] = reference_hex.properties["owned"]
        feature.properties["owner"] = reference_hex.properties["owner"]
        feature.properties["ownership_change"] = reference_hex.properties["ownership_change"]
        """
        try:
            feature.properties["neighbours"] = reference_hex.properties["neighbours"]
        except KeyError:
            continue
    with open(os.path.join(path, 'hexagons%d.geojson' % turn),
              'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    return


def update_ownership(feature):
    feature.properties["owner"] = "Something new"
    return feature


def test(hexagons):
    for feature in hexagons.features:
        print(feature.properties["owner"])
        feature = update_ownership(feature)
        print(feature.properties["owner"])
    return


def main():
    turn=0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    """
    hexagons = owner.determine_neighbours(hexagons)
    hexagons = owner.generate_ownership(hexagons)
    hexagons = owner.determine_ownership(hexagons)
    with open(os.path.join(test_path, 'hexagons%d.geojson' % turn),
              'w') as f:
        geojson.dump(hexagons, f, sort_keys=True, indent=2)
    """
    turn += 1
    for turn in range (1, 8):
        fix(hexagons, test_path, turn=turn)
    
    #test(hexagons)
    return


if __name__ == '__main__':
    main()