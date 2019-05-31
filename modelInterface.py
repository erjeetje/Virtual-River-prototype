# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:21:54 2019

@author: HaanRJ
"""


import time
import geojson
import bmi.wrapper
import matplotlib.pyplot as plt
import numpy as np
import gridMapping as gridmap
import updateRoughness as roughness
from copy import deepcopy


def initialize_model():
    model = bmi.wrapper.BMIWrapper('dflowfm')
    model.initialize(r'C:\Users\HaanRJ\Documents\GitHub\sandbox-fm\models\sandbox\Waal_schematic\waal_with_side.mdu')
    print('model initialized')
    return model


def run_model(model, filled_node_grid, face_grid, hexagons):
    model.get_var('s1')
    #numk = model.get_var('numk')
    #ndx = model.get_var('ndx')
    ndxi = model.get_var('ndxi')
    
    # points, nodes, vertices (corner points)
    xk = model.get_var('xk')
    yk = model.get_var('yk')
    
    # cell centers
    xzw = model.get_var('xzw')
    yzw = model.get_var('yzw')
    
    # on the nodes
    zk = model.get_var('zk')
    
    # on the faces/cells (including boundary points)
    s1 = model.get_var('s1')[:ndxi]
    ucx = model.get_var('ucx')[:ndxi]
    ucy = model.get_var('ucy')[:ndxi]

    s1_t0 = s1.copy()
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
    sc = axes[0].scatter(xzw, yzw, c=s1, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    sc_zk = axes[1].scatter(xk, yk, c=zk, edgecolor='none', vmin=0, vmax=6, cmap='jet')

    plt.show()
    zk_new = np.array([feature.properties['z'] for feature in filled_node_grid['features']])
    for i in range(10):
        model.update()
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(s1.copy())
        sc_zk.set_array(zk.copy())
        plt.draw()
        plt.pause(0.00001)
    qv = axes[1].quiver(xzw, yzw, ucx, ucy)
    changed = [
            feature
            for feature
            in filled_node_grid.features
            if feature.properties['changed']
    ]
    frcu = model.get_var('frcu')
    test = np.unique(deepcopy(frcu))
    print(test)
    """
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    default_landuse = 8
    for feature in filled_node_grid.features:
        feature.properties["landuse"] = default_landuse
        if feature.properties["board"]:
            location = feature.properties["location"]
        else:
            continue
        hexagon = hexagons_by_id[location]
        landuse = hexagon.properties["landuse"]
        # for now use z
        if hexagon.properties['z'] == 0:
            landuse = 9
        else:
            landuse = 8
        feature.properties["landuse"] = landuse
    for feature in filled_node_grid.features:
        friction = landuse_to_friction(feature.properties['landuse'])
        frcu[feature.id] = friction
    """
    if True:
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64') * 1.5
            model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
            )
    s0 = s1.copy()
    model.update(60)
    for i in range(50):
        model.update(3)
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(s1.copy() - s0)
        sc_zk.set_array(zk.copy())
        qv.set_UVC(ucx.copy(), ucy.copy())
        plt.draw()
        plt.pause(0.00001)

    print(model.get_current_time())


def landuse_to_friction(landuse):
    if landuse == 9:
        friction = 1000
    else:
        friction = 1
    return friction


if __name__ == "__main__":
    save = False
    turn = 0
    plt.interactive(True)
    calibration = gridmap.read_calibration()
    t0 = time.time()
    hexagons = gridmap.read_hexagons(filename='hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["changed"] = True
    t1 = time.time()
    print("Read hexagons: " + str(t1 - t0))
    model = initialize_model()
    node_grid = gridmap.read_node_grid()
    face_grid = gridmap.read_face_grid(model)
    t2 = time.time()
    print("Load grid: " + str(t2 - t1))
    node_grid = gridmap.index_node_grid(hexagons, node_grid)
    face_grid = gridmap.index_face_grid(hexagons, face_grid)
    t3 = time.time()
    print("Index grid: " + str(t3 - t2))
    node_grid = gridmap.interpolate_node_grid(hexagons, node_grid)
    hexagons, face_grid = roughness.hex_to_points(model, hexagons, face_grid)
    with open('node_grid_before%d.geojson' % turn, 'w') as f:
        geojson.dump(node_grid, f, sort_keys=True,
                     indent=2)
    t4 = time.time()
    print("Interpolate grid: " + str(t4 - t3))
    filled_node_grid = deepcopy(node_grid)
    filled_hexagons = deepcopy(hexagons)
    filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
    t5 = time.time()
    print("Hexagons to fill: " + str(t5 - t4))
    filled_node_grid = gridmap.update_node_grid(filled_hexagons, filled_node_grid,
                                        fill=True)
    t6 = time.time()
    print("Nodes to fill: " + str(t6 - t5))
    filled_node_grid = gridmap.interpolate_node_grid(filled_hexagons, filled_node_grid,
                                             turn=turn)
    t7 = time.time()
    print("Interpolated filled grid: " + str(t7 - t6))
    if save:
        with open('node_grid_after%d.geojson' % turn, 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open('filled_node_grid%d.geojson' % turn, 'w') as f:
            geojson.dump(filled_node_grid, f, sort_keys=True,
                         indent=2)
    t8 = time.time()
    if save:
        print("Saved both grids: " + str(t8 - t7))
    gridmap.create_geotiff(node_grid)
    t9 = time.time()
    print("Created geotiff: " + str(t9 - t8))
    run_model(model, filled_node_grid, face_grid, hexagons)
