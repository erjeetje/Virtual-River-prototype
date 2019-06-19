# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 10:48:55 2019

@author: HaanRJ
"""

import os
import time
#import gridMapping as gridmap
import matplotlib.pyplot as plt
import bmi.wrapper
import cv2


def initialize_model():
    print("I am here")
    model = None
    model = bmi.wrapper.BMIWrapper('dflowfm')
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    model_name = 'waal_with_side.mdu'
    model_path = os.path.join(dir_path, 'models', 'Waal_schematic', model_name)
    model.initialize(model_path)
    """
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
    print(ucx)

    """
    s1_t0 = s1.copy()
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
    sc = axes[0].scatter(xzw, yzw, c=s1, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    sc_zk = axes[1].scatter(xk, yk, c=zk, edgecolor='none', vmin=0, vmax=6, cmap='jet')

    plt.show()
    zk_new = np.array([feature.properties['z'] for feature in filled_node_grid['features']])
    for i in range(10):
        model.update()
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(ucx.copy())
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
        sc.set_array(ucx.copy())
        sc_zk.set_array(zk.copy())
        qv.set_UVC(ucx.copy(), ucy.copy())
        plt.draw()
        plt.pause(0.00001)

    print(model.get_current_time())
    
    ucx = model.get_var('ucx')[:ndxi]
    ucy = model.get_var('ucy')[:ndxi]
    generate_geojson(ucx)
    generate_geojson(ucy)
    """
    return


if __name__ == "__main__":
    """
    save = False
    turn = 0
    #plt.interactive(True)
    print("I am here 4")
    calibration = gridmap.read_calibration()
    print("I am here 5")
    t0 = time.time()
    hexagons = gridmap.read_hexagons(filename='storing_files\\hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
    model = initialize_model()
    print("I am here 6")
    node_grid = gridmap.read_node_grid()
    print("I am here 7")
    face_grid = gridmap.read_face_grid(model)
    """
    
    model = initialize_model()
    