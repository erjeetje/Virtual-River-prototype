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
import updateRoughness as roughness
from copy import deepcopy
from shapely import geometry

class Model():
    def __init__(self):
        self.model = self.initialize_model()
        self.fig = None
        self.axes = None
        self.node_index = None
        self.face_index = None
        plt.interactive(True)
        #plt.ion()

    def initialize_model(self):
        """
        Function to initialize the model using bmi. If the Virtual River is copied
        including the models folder, no changes are needed.
        """
        model = bmi.wrapper.BMIWrapper('dflowfm')
        dir_path = os.path.dirname(os.path.realpath(__file__))
        model_name = 'Virtual_River.mdu'
        model_path = os.path.join(dir_path, 'models', 'Waal_schematic', model_name)
        model.initialize(model_path)
        print('Initialized Delft3D FM model.')
        return model
    
    def set_indexes(self, node_grid, face_grid):
        def index(grid):
            x_left_board = -400
            x_right_board = 400
            y_bottom_board = -300
            x_top_board = 300
            indexes = []
            for feature in grid.features:
                shape = shape = geometry.asShape(feature.geometry)
                x = shape.centroid.x
                y = shape.centroid.y
                if ((x >= x_left_board and x <= x_right_board) and
                    (y >= y_bottom_board and y <= x_top_board)):
                    indexes.append(feature.id)
            return indexes
        self.node_index = np.array(index(node_grid))
        self.face_index = np.array(index(face_grid))
        return

    def run_model(self, filled_node_grid, hexagons, flow_grid, vert_scale, turn=0, blit=False):
        """
        Function that runs the model. Currently gets the variables from the model,
        updates the variables (e.g. zk to update the elevation model). Subsequently
        updates the model.
        
        Once changes have been made (e.g. to running the model in the cloud), this
        function should be updated. Should probably be separated into multiple
        functions as well.
        """
        self.model.get_var('s1')
        #numk = model.get_var('numk')
        #ndx = model.get_var('ndx')
        ndxi = self.model.get_var('ndxi')
        
        # points, nodes, vertices (corner points)
        xk = self.model.get_var('xk')
        yk = self.model.get_var('yk')
        
        # cell centers
        xzw = self.model.get_var('xzw')
        yzw = self.model.get_var('yzw')
        
        # on the nodes
        zk = self.model.get_var('zk')
        
        # on the faces/cells (including boundary points)
        s1 = self.model.get_var('s1')[:ndxi]
        ucx = self.model.get_var('ucx')[:ndxi]
        ucy = self.model.get_var('ucy')[:ndxi]
        
        colorbar = False

        if True:
            self.fig, self.axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
            colorbar = True

        self.sc = self.axes[0].scatter(
                xzw[self.face_index], yzw[self.face_index],
                c=s1[self.face_index], edgecolor='none', vmin=0, vmax=6,
                cmap='jet')
        self.sc_zk = self.axes[1].scatter(
                xk[self.node_index], yk[self.node_index],
                c=zk[self.node_index], edgecolor='none', vmin=0, vmax=6,
                cmap='jet')
        self.axes[0].set_aspect('equal')
        self.axes[1].set_aspect('equal')
        if colorbar:
            self.fig.colorbar(self.sc, ax=self.axes[0])
            self.fig.colorbar(self.sc_zk, ax=self.axes[1])
        plt.show()

        self.qv = self.axes[1].quiver(
                xzw[self.face_index], yzw[self.face_index],
                ucx[self.face_index], ucy[self.face_index])
        changed = [
                feature
                for feature
                in filled_node_grid.features
                if feature.properties['changed']
        ]
    
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64')  # * 1.5
            self.model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
                    )
        #s0 = s1.copy()
        print("updated grid in model")
        if blit:
            background1 = self.fig.canvas.copy_from_bbox(self.axes[0])
            background2 = self.fig.canvas.copy_from_bbox(self.axes[1])
        
        self.sc_zk.set_array(zk[self.node_index].copy())
        if turn == 0:
            step = 120
        else:
            step = 50
        for i in range(step):
            if i % 10 == 0:
                self.update_waterlevel(hexagons)
                hexagons = roughness.landuse_to_friction(hexagons, vert_scale=vert_scale)
                hexagons, flow_grid = roughness.hex_to_points(
                self.model, hexagons, flow_grid)
                print("Executed model initiation loop " + str(i/10) + ", updating roughness.")
            t0 = time.time()
            self.model.update(25)
            t1 = time.time()
            print("model update: " + str(t1 - t0))
            self.axes[0].set_title("{:2f}".format(self.model.get_current_time()))
            #t2 = time.time()
            #print("axes title: " + str(t2 - t1))
            self.sc.set_array(s1[self.face_index].copy())
            #t3 = time.time()
            #print("set sc: " + str(t3 - t2))
            #self.sc_zk.set_array(zk.copy())
            #t4 = time.time()
            #print("set sc_zk: " + str(t4 - t3))
            self.qv.set_UVC(ucx[self.face_index].copy(), ucy[self.face_index].copy())
            #t5 = time.time()
            #print("set qv: " + str(t5 - t4))
            #plt.draw()
            if blit:
                self.fig.canvas.restore_region(background1)
                self.fig.canvas.restore_region(background2)
                
                self.axes[0].draw_artist(self.sc)
                self.axes[1].draw_artist(self.qv)
                
                self.fig.canvas.blit(self.axes[0].bbox)
                self.fig.canvas.blit(self.axes[1].bbox)
            else:
                self.fig.canvas.draw()
            #t6 = time.time()
            #print("draw: " + str(t6 - t5))
            plt.pause(0.00001)
            t7 = time.time()
            print("loop time: " + str(t7 - t0))
    
        print("Finished run model. Current time in model: " +
              str(self.model.get_current_time()))
        return hexagons, flow_grid
    
    
    def update_waterlevel(self, hexagons):
        s1 = self.model.get_var('s1')
        for feature in hexagons.features:
            index = feature.properties["face_cell"]
            feature.properties["water_level"] = s1[index]
        return hexagons


def geojson2pli(collection, name="structures"):
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
        #feature.properties["pli_path"] = pli_path
        feature.properties["pli_path"] = filename
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
