# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:21:54 2019

@author: HaanRJ
"""


import os
import time
import geojson
import bmi.wrapper
import mako.template
import matplotlib.pyplot as plt
import numpy as np
import gridMapping as gridmap
from copy import deepcopy


def initialize_model():
    """
    Function to initialize the model using bmi. If the Virtual River is copied
    including the models folder, no changes are needed.
    """
    model = bmi.wrapper.BMIWrapper('dflowfm')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    model_name = 'waal_with_side.mdu'
    model_path = os.path.join(dir_path, 'models', 'Waal_schematic', model_name)
    model.initialize(model_path)
    #model.initialize(r'C:\Users\HaanRJ\Documents\GitHub\sandbox-fm\models\sandbox\Waal_schematic\waal_with_side.mdu')
    print('model initialized')
    return model


def run_model(model, filled_node_grid, face_grid, hexagons, fig=None,
              axes=None, initialized=False):
    """
    Function that runs the model. Currently gets the variables from the model,
    updates the variables (e.g. zk to update the elevation model). Subsequently
    updates the model.
    
    Once changes have been made (e.g. to running the model in the cloud), this
    function should be updated. Should probably be separated into multiple
    functions as well.
    """
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
    #frcu = model.get_var('frcu')[:ndxi]

    #s1_t0 = s1.copy()
    
    #print(min(frcu))
    #print(max(frcu))

    if fig is None:
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
        plt.figure()
    sc = axes[0].scatter(xzw, yzw, c=s1, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    sc_zk = axes[1].scatter(xk, yk, c=zk, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    if not initialized:
        fig.colorbar(sc, ax=axes[0])
        fig.colorbar(sc_zk, ax=axes[1])

    plt.show()
    #zk_new = np.array([feature.properties['z'] for feature in filled_node_grid['features']])
    """
    for i in range(10):
        model.update()
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(ucx.copy())
        sc_zk.set_array(zk.copy())
        plt.draw()
        plt.pause(0.00001)
    """
    #qv = axes[0].quiver(xzw, yzw, ucx, ucy)
    qv = axes[1].quiver(xzw, yzw, ucx, ucy)
    changed = [
            feature
            for feature
            in filled_node_grid.features
            if feature.properties['changed']
    ]

    if True:
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64') * 1.5
            model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
            )
    #s0 = s1.copy()
    print("updated grid in model")
    if not initialized:
        model.update(10)
    #print("set timesteps in model")
    for i in range(100):
        #t0 = time.time()
        model.update(5)
        #t1 = time.time()
        #print("model update: " + str(t1 - t0))
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        #t2 = time.time()
        #print("axes title: " + str(t2 - t1))
        sc.set_array(s1.copy())
        #t3 = time.time()
        #print("set sc: " + str(t3 - t2))
        sc_zk.set_array(zk.copy())
        #t4 = time.time()
        #print("set sc_zk: " + str(t4 - t3))
        qv.set_UVC(ucx.copy(), ucy.copy())
        #t5 = time.time()
        #print("set qv: " + str(t5 - t4))
        plt.draw()
        #t6 = time.time()
        #print("draw: " + str(t6 - t5))
        plt.pause(0.00001)

    print(model.get_current_time())
    return fig, axes


def geojson2pli(collection, name="groyne"):
    """
    convert geojson input (FeatureCollection of linestring features) to an ini
    file listing all structures.
    """
    structures_template_text = '''
%for feature in features:
[structure]
type                  = weir                # Type of structure
id                    = ${feature.id}              # Name of the structure
polylinefile          = ${feature.properties["pli_path"]}          # *.pli; Polyline geometry definition for 2D structure
crest_level           = ${feature.properties["crest_level"]}            # Crest height in [m]
crest_width           = 
lat_contr_coeff       = 1                   # Lateral contraction coefficient in 
%endfor
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(dir_path, 'models', 'Waal_schematic')
    for feature in collection.features:
        filename = (str(feature.id) + '.pli')
        #path = pathlib.Path(feature.id)
        #pli_path = path.with_suffix('.pli').relative_to(path.parent)
        pli_path = os.path.join(model_path, filename)
        create_pli(feature, pli_path)
        feature.properties["pli_path"] = pli_path
    structures_template = mako.template.Template(structures_template_text)
    #path = pathlib.Path(name)
    #structures_path = path.with_suffix('.ini').relative_to(path.parent)
    filename = (name + '.ini')
    with open(os.path.join(model_path, filename), 'w') as f:
        rendered = structures_template.render(features=collection.features)
        f.write(rendered)
    return


def create_pli(feature, pli_path):
    """
    convert geojson input (FeatureCollection of linestring features) to a pli
    file that is referenced to in the ini file.
    """
    pli_template_text = '''${structure_id}
${len(coordinates)} 2
%for point in coordinates:
${point[0]} ${point[1]}
%endfor
'''
    pli_template = mako.template.Template(pli_template_text)
    with open(pli_path, 'w') as f:
        rendered = pli_template.render(structure_id=feature.id,
                                       coordinates=feature.geometry.coordinates)
        f.write(rendered)
    return


if __name__ == "__main__":
    save = False
    turn = 0
    plt.interactive(True)
    calibration = gridmap.read_calibration()
    t0 = time.time()
    hexagons = gridmap.read_hexagons(filename='storing_files\\hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
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
    #hexagons, face_grid = roughness.hex_to_points(model, hexagons, face_grid,
    #                                              test=True)
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
    filled_node_grid = gridmap.update_node_grid(filled_hexagons,
                                                filled_node_grid,
                                                fill=True)
    t6 = time.time()
    print("Nodes to fill: " + str(t6 - t5))
    filled_node_grid = gridmap.interpolate_node_grid(filled_hexagons,
                                                     filled_node_grid,
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
    fig, axes = run_model(model, filled_node_grid, face_grid, hexagons,
                          initialized=False)
    print("going to run it again!")
    for feature in filled_node_grid.features:
        feature.properties['changed'] = False
    fig, axes = run_model(model, filled_node_grid, face_grid, hexagons,
                          initialized=True, fig=fig, axes=axes)
