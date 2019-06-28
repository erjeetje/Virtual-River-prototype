# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 12:51:17 2019

@author: HaanRJ
"""

import time
import geojson
import numpy as np
import modelInterface as D3D


def create_flow_grid(model, save=False, path=""):
    """
    function that loads the face grid (centers of the cells) and the ln values
    (the links between cells) and transforms them into (x, y) positions of the
    the flow links grid.
    """
    x = model.get_var('xzw')
    y = model.get_var('yzw')
    frcu = model.get_ver('frcu')
    print(len(x), len(frcu))
    xy = np.c_[x, y]
    features = []
    for i, xy_i in enumerate(xy):
        pt = geojson.Point(coordinates=list(xy_i))
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open(os.path.join(path, 'face_grid.geojson'), 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def create_flow_grid(model, save=False):
    ln = model.get_var('ln')
    x = model.get_var('xzw')
    y = model.get_var('yzw')
    flow_links = []
    skipped = 0
    for i, item in enumerate(ln):
        try:
            cell1_x = x[item[0]-1]
            cell1_y = y[item[0]-1]
            cell2_x = x[item[1]-1]
            cell2_y = y[item[1]-1]
            flow_x = (cell1_x + cell2_x) / 2.0
            flow_y = (cell1_y + cell2_y) / 2.0
            flow_links.append([flow_x, flow_y])
        except IndexError:
            skipped += 1
            continue
    print("NOTE: ", str(skipped), " flow links skipped as unknown cells were ",
          "called. Skipped cells are irrelevant for the board.")
    features = []
    for i, xy in enumerate(flow_links):
        pt = geojson.Point(coordinates=xy)
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open('flowlinks_grid.geojson', 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def main(save=False):
    model = D3D.initialize_model()
    frcu = model.get_var('frcu')
    print("frcu length:", len(frcu), "frcu shape", frcu.shape)
    """
    lnx1D = model.get_var('lnx1D')
    print(lnx1D)
    #print("lnx1D length:", len(lnx1D), "lnx1D shape", lnx1D.shape)
    lnxi = model.get_var('lnxi')
    print(lnxi)
    #print("lnxi length:", len(lnxi), "lnxi shape", lnxi.shape)
    lnx1Db = model.get_var('lnx1Db')
    print(lnx1Db)
    #print("lnx1Db length:", len(lnx1Db), "lnx1Db shape", lnx1Db.shape)
    lnx = model.get_var('lnx')
    print(lnx)
    #print("lnx length:", len(lnx), "lnx shape", lnx.shape)
    """
    start = time.time()
    ln = model.get_var('ln')
    """
    with open('ln_test.txt', 'w') as f:
        for i, item in enumerate(ln):
            f.write(str(i) + ": " + str(item) + '\n')
    """
    x = model.get_var('xzw')
    y = model.get_var('yzw')

    """
    xy = np.c_[x, y]
    xy = xy[:len(xy)]
    with open('xy_test.txt', 'w') as f:
        for i, item in enumerate(xy):
            f.write(str(i) + ": " + str(item) + '\n')
    """


    flow_links = []
    #grid_size = len(x)
    skipped = 0
    for i, item in enumerate(ln):
        try:
            cell1_x = x[item[0]-1]
            cell1_y = y[item[0]-1]
            cell2_x = x[item[1]-1]
            cell2_y = y[item[1]-1]
            flow_x = (cell1_x + cell2_x) / 2.0
            flow_y = (cell1_y + cell2_y) / 2.0
            flow_links.append([flow_x, flow_y])
        except IndexError:
            skipped += 1
            continue
    print(skipped)
    #flow_links = np.array(flow_links)
    features = []
    for i, xy in enumerate(flow_links):
        pt = geojson.Point(coordinates=xy)
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open('flowlinks_grid.geojson', 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)

    """
    lncn = model.get_var('lncn')
    print(lncn)
    print("lncn length:", len(lncn), "lncn shape", lncn.shape)
    kn = model.get_var('kn')
    print(kn)
    print("kn length:", len(kn), "ln shape", kn.shape)
    """
    """
    edgenumbers1d2d = model.get_var('edgenumbers1d2d')
    print(edgenumbers1d2d)
    print("edgenumbers1d2d length:", len(edgenumbers1d2d), "edgenumbers1d2d shape", edgenumbers1d2d.shape)
    """


if __name__ == "__main__":
    main()