# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 21:24:05 2019

@author: HaanRJ
"""


import os
import json
import cv2
import numpy as np
import scipy.spatial
import modelInterface as D3D
import gridMapping as gridmap
import updateRoughness as roughness


def transform(x, y, M):
    """perspective transform x,y with M"""
    xy_t = np.squeeze(
        cv2.perspectiveTransform(
            np.dstack(
                [
                    x,
                    y
                ]
            ),
            np.asarray(M)
        )
    )
    return xy_t[:, 0], xy_t[:, 1]


class Visualization():
    def __init__(self, model, node_grid, face_grid):
        self.model = model
        
        self.data = {}

        self.config = self.read_config()

        WIDTH = self.config['settings']['width']
        HEIGHT = self.config['settings']['height']

        self.default_box = np.array([
            [0, 0],
            [WIDTH, 0],
            [WIDTH, HEIGHT],
            [0, HEIGHT]
        ], dtype='float32')

        self.model_box = np.array([
            [-600, -400],
            [600, -400],
            [600, 400],
            [-600, 400]
        ], dtype='float32')


        self.transforms = self.compute_transforms()

        self.data.update(
            self.update_initial_vars(model=model)
        )

        
        self.grid = self.init_grid()
        self.init_screens()
        print("I work!")
    
    
    def read_config(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, "screens.json")) as f:
            config = json.load(f)
        return config
    
    
    def compute_transforms(self):
        """compute transformation matrices based on calibration data"""

        point_names = [
            "model",
            "box"
        ]

        point_arrays = {}
        point_arrays['box'] = self.default_box
        point_arrays['model'] = self.model_box

        transforms = {}
        for a in point_names:
            for b in point_names:
                if a == b:
                    continue
                if not (a in point_arrays):
                    continue
                if not (b in point_arrays):
                    continue
                transform_name = a + '2' + b
                transform = cv2.getPerspectiveTransform(
                    point_arrays[a],
                    point_arrays[b]
                )
                transforms[transform_name] = transform

        return transforms
    
    
    def update_initial_vars(self, model=None, engine='dflowfm_nc'):
        """get the initial variables for the model"""
        # variables on t=0
        data = {}
        meta = {"initial_vars": [
        'xzw',
        'yzw',
        'xk',
        'yk',
        'zk',
        'ndx',
        'ndxi',             # number of internal points (no boundaries)
        'flowelemnode'
        ],
        "vars": ['bl', 'ucx', 'ucy', 's1', 'zk'],
        }
        for name in meta['initial_vars']:
            """
            if engine.endswith('_nc'):
                data[name] = self.ds.variables[name][:]
            else:
            """
            data[name] = model.get_var(name)

        for name in meta['vars']:
            """
            if engine.endswith('_nc'):
                data[name] = self.ds.variables[name][:]
            else:
            """
            data[name] = model.get_var(name)
            data[name + '_0'] = model.get_var(name).copy()
        meta['compute'](data)
        for key, val in meta["mapping"].items():
            data[key] = data[val]
        return data
    
    
    def init_grid(self):
        """initialize grid variables"""

        # rename  some vars
        data = {}

        WIDTH = self.config['settings']['width']
        HEIGHT = self.config['settings']['height']
        
        # column and row numbers
        n, m = np.mgrid[:HEIGHT, :WIDTH]
        # transformed to model coordinates
        m_t, n_t = transform(
            m.ravel().astype('float32'),
            n.ravel().astype('float32'),
            self.transforms['box2model']
        )

        # lookup  closest cells
        cell_centers = np.c_[
            self.data['X_CELLS'].ravel(),
            self.data['Y_CELLS'].ravel()
        ]
        tree = scipy.spatial.cKDTree(cell_centers)
        distances_cells, ravensburger_cells = tree.query(np.c_[m_t, n_t])
        data['ravensburger_cells'] = ravensburger_cells.reshape(HEIGHT, WIDTH)
        data['distances_cells'] = distances_cells.reshape(HEIGHT, WIDTH)

        # lookup closest nodes
        nodes = np.c_[
            self.data['X_NODES'].ravel(),
            self.data['Y_NODES'].ravel()
        ]
        tree = scipy.spatial.cKDTree(nodes)
        distances_nodes, ravensburger_nodes = tree.query(np.c_[m_t, n_t])
        data['ravensburger_nodes'] = ravensburger_nodes.reshape(HEIGHT, WIDTH)
        data['distances_nodes'] = distances_nodes.reshape(HEIGHT, WIDTH)

        # not sure what this does....
        data['node_mask'] = data['distances_nodes'] > 500
        data['cell_mask'] = data['distances_cells'] > 500

        # cell centers
        x_cells_box, y_cells_box = transform(
            self.data['X_CELLS'].ravel(),
            self.data['Y_CELLS'].ravel(),
            self.transforms['model2box']
        )
        data['x_cells_box'] = x_cells_box
        data['y_cells_box'] = y_cells_box
        return data
    
    
    def init_screens(self):
        # Initialize
        self.screen = self.config['screens'][0]
        # Create a debug screen so you can see what's going on.
        cv2.namedWindow('debug', flags=cv2.WINDOW_NORMAL)
        # Create a main window for the beamer
        cv2.namedWindow('main', flags=cv2.WINDOW_NORMAL)
        # make main window full screen
        if self.config['settings'].get('fullscreen', False):
            cv2.setWindowProperty('main', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def main():
    """
    hexagons = gridmap.read_hexagons(filename='storing_files\\hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
    hexagons = gridmap.hexagons_to_fill(hexagons)
    """
    model = D3D.initialize_model()
    """
    node_grid = gridmap.read_node_grid()
    face_grid = gridmap.read_face_grid(model)
    node_grid = gridmap.index_node_grid(hexagons, node_grid)
    face_grid = gridmap.index_face_grid(hexagons, face_grid)
    node_grid = gridmap.interpolate_node_grid(hexagons, node_grid)
    hexagons, face_grid = roughness.hex_to_points(model, hexagons, face_grid,
                                                  test=True)
    """
    viz = Visualization(model, node_grid, face_grid)
    
    #viz.loop()
    #viz.close()
    
    
if __name__ == '__main__':
    main()