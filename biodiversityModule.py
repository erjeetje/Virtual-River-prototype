# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:47:18 2019

@author: HaanRJ
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
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
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
    polygons = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        poly = feature.geometry.coordinates[0]
        polygon = Polygon(poly, False, fill=False, linewidth=0.5)
        polygons.append(polygon)
    p = PatchCollection(polygons, facecolors=None, alpha=0.4)
    colors = 100*np.random.rand(len(polygons))
    p.set_array(np.array(colors))
    axes[0].add_collection(p)
    fig.colorbar(p, ax=axes[0])
    axes[0].set_xlim([-400, 400])
    axes[0].set_ylim([-300, 300])
    axes[1].set_xlim([-400, 400])
    axes[1].set_ylim([-300, 300])
    """
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
    """
    return
    
if __name__ == '__main__':
    main()