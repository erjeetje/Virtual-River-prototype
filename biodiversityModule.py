# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:47:18 2019

@author: HaanRJ
"""

import os
import numpy as np
import pandas as pd
import gridMapping as gridmap
from pandas.io.json import json_normalize


def set_ecotope(hexagons):
    for feature in hexagons.features:
        z = feature.properties["z"]
        landuse = feature.properties["landuse"]
        if (z == 0 and landuse == 9):
            feature.properties["ecotope"] = "hoofdgeul kribvak"
        elif (z == 0 and landuse == 8):
            feature.properties["ecotope"] = "hoofdgeul overgeul"
    return hexagons



def main():
    turn=0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'temp_files')
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    df = json_normalize(hexagons.features)
    cols = ["properties.z_reference", "properties.landuse", "properties.biosafe"]
    df = df.loc[:,cols]
    df.columns = ["z_reference", "landuse" ,"biosafe"]
    print(df)
    test = df.groupby('landuse').sum()
    print(test)
    test2 = test.z_reference
    print(test2)
    #hexagons = set_ecotope(hexagons)
    #print(hexagons.features)
    #test = hexagons.features[0]
    #print(test)
    
    #test = pd.DataFrame(test.properties)
    #test = {}
    #for feature in hexagons.features:
    #    test.update([feature.id: ])
    #test = pd.read_json(hexagons.features.properties)
    #print(test)
    return
    
if __name__ == '__main__':
    main()