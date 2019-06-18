import time
import json
import itertools

import click
import cv2

import numpy as np
import matplotlib.cm
import matplotlib.colors
import netCDF4
import scipy.spatial


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

def dflowfm_compute(data):
    """compute variables that are missing/buggy/not available"""
    numk = data['zk'].shape[0]
    data['numk'] = numk
    # fix shapes
    for var_name in dflowfm_vars:
        arr = data[var_name]
        if arr.shape[0] == data['numk']:
            data[var_name] = arr[:data['numk']]
        elif arr.shape[0] == data['ndx']:
            "should be of shape ndx"
            # ndxi:ndx are the boundary points
            # (See  netcdf write code in unstruc)
            data[var_name] = arr[:data['ndxi']]
            # data should be off consistent shape now
        elif arr.shape[0] == data['ndxi']:
            # this is ok
            pass
        else:
            msg = "unexpected data shape %s for variable %s" % (
                arr.shape,
                var_name
            )
            raise ValueError(msg)
        # compute derivitave variables, should be consistent shape now.
    data['is_wet'] = data['s1'] > data['bl']

def update_height_dflowfm(idx, height_nodes_new, data, model):
    nn = 0
    for i in np.where(idx)[0]:
        # Only update model where the bed level changed (by compute_delta_height)
        if height_nodes_new[i] < data['bedlevel_update_maximum'] and np.abs(height_nodes_new[i] - data['HEIGHT_NODES'][i]) > data['bedlevel_update_threshold']:
            nn += 1
            model.set_var_slice('zk', [int(i+1)], [1], height_nodes_new[i:i + 1])
    print('Total bed level updates', nn)

#  a list of mappings of variables
# variables are not named consistently between models and between netcdf files and model
dflowfm = {
    "initial_vars": [
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
    "mapping": dict(
        X_NODES="xk",
        Y_NODES="yk",
        X_CELLS="xzw",
        Y_CELLS="yzw",
        HEIGHT_NODES="zk",
        HEIGHT_CELLS="bl",
        WATERLEVEL="s1",
        U="ucx",
        V="ucy"
    ),
    "compute": dflowfm_compute,
    "update_nodes": update_height_dflowfm
}
dflowfm["reverse_mapping"] = {value: key for key, value in dflowfm["mapping"].items()}


dflowfm_nc = {
    "initial_vars": [
        'mesh2d_face_x',
        'mesh2d_face_y',
        'mesh2d_node_x',
        'mesh2d_node_y',
        'mesh2d_node_z'
    ],
    "vars": ['mesh2d_flowelem_bl', 'mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_s1', 'mesh2d_node_z'],
    "mapping": dict(
        X_NODES="mesh2d_node_x",
        Y_NODES="mesh2d_node_y",
        X_CELLS="mesh2d_face_x",
        Y_CELLS="mesh2d_face_y",
        HEIGHT_NODES="mesh2d_node_z",
        HEIGHT_CELLS="mesh2d_flowelem_bl",
        WATERLEVEL="mesh2d_s1",
        U="mesh2d_ucx",
        V="mesh2d_ucy"
    ),
    "compute": lambda x: x,
    "update_nodes": lambda x: x
}
dflowfm_nc["reverse_mapping"] = {value: key for key, value in dflowfm["mapping"].items()}

available = {
    "dflowfm": dflowfm,       # from memory
    "dflowfm_nc": dflowfm_nc  # from file
}


def get_data(t=0, nx=500, ny=300):
    """generate some initial data"""
    # TODO: get this from the model
    ds = netCDF4.Dataset('models/Waal_schematic/DFM_OUTPUT_waal_with_side/waal_with_side_map.nc')
    ucx = ds.variables['mesh2d_ucx'][t].reshape(133, 200)
    ucy = ds.variables['mesh2d_ucy'][t].reshape(133, 200)
    s1 = ds.variables['mesh2d_s1'][t].reshape(133, 200)
    return dict(
        ucx=ucx,
        ucy=ucy,
        s1=s1
    )


class Visualization():
    def __init__(self, ds):
        self.ds = ds
        
        self.data = {}

        self.config = self.read_config()
        print(self.config)

        WIDTH = self.config['settings']['width']
        HEIGHT = self.config['settings']['height']

        self.default_box = np.array([
            [0, 0],
            [WIDTH, 0],
            [WIDTH, HEIGHT],
            [0, HEIGHT]
        ], dtype='float32')

        self.model = np.array([
            [-600, -400],
            [600, -400],
            [600, 400],
            [-600, 400]
        ], dtype='float32')

        self.transforms = self.compute_transforms()
        self.data.update(
            self.update_initial_vars()
        )
        self.grid = self.init_grid()
        
        
    def read_config(self):
        with open("screens.json") as f:
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
        point_arrays['model'] = self.model

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
        meta = available[engine]
        for name in meta['initial_vars']:
            if engine.endswith('_nc'):
                data[name] = self.ds.variables[name][:]
            else:
                data[name] = model.get_var(name)

        for name in meta['vars']:
            if engine.endswith('_nc'):
                data[name] = self.ds.variables[name][:]
            else:
                data[name] = model.get_var(name)
                data[name + '_0'] = model.get_var(name).copy()
        meta['compute'](data)
        for key, val in meta["mapping"].items():
            data[key] = data[val]
        return data


    def update_vars(data, model=None, engine='dflowfm_nc', t=0):
        """get the variables from the model and put them in the data dictionary"""
        meta = available[engine]
        for name in meta['vars']:
            if engine.endswith('_nc'):
                # assume t is first dimension
                data[name] = self.ds.variables[name][t]
            else:
                data[name] = model.get_var(name)
        # do some stuff per model
        meta["compute"](data)
        for key, val in meta["mapping"].items():
            data[key] = data[val]

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

def imshow_layer(data, layer, window='main'):
    # get the variable for this layer
    var = data[layer['variable']]
    # get min and max if set
    min = layer.get('min', var.min())
    max = layer.get('max', var.max())
    # the normalization function
    N = matplotlib.colors.Normalize(var.min(), var.max())
    # the colormap
    cmap = getattr(matplotlib.cm, layer['colormap'])
    # the colored image
    rgba = cmap(N(var))

    # TODO: check if we can do this with opencv (convert or something...)
    rgb = np.uint8(rgba * 256)[...,:3]
    
    # this is one plot, other variants might include advection of colors 
    cv2.imshow(window, rgb)



def viz_loop():
    """run the main visualization loop"""

    # Read visualization configuration
    # Visualization types -> list of layers
    with open("screens.json") as f:
        config = json.load(f)

    print(config)
    screens = config['screens']

    # Initialize 
    # Create a debug screen so you can see what's going on.
    cv2.namedWindow('debug', flags=cv2.WINDOW_OPENGL | cv2.WINDOW_NORMAL)
    # Create a main window for the beamer
    cv2.namedWindow('main', flags=cv2.WINDOW_OPENGL | cv2.WINDOW_NORMAL)
    # make main window full screen
    if config['settings'].get('fullscreen', False):
        cv2.setWindowProperty('main', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    screen = screens[0]
    
    # Load initial data
    initial_data = get_data(t=0)
    # Create initial visualization (type)
    for layer in screen['layers']:
        imshow_layer(data=initial_data, layer=layer, window='main')

    # for now create a list of variables:

    # We have three event loops in parallel.
    
    # [VIZ] loop
    # Process input (click, key)
    # If visualization type changed: Create initial visualization
    # Update visualization

    for i in itertools.count():
        key = cv2.waitKey(1)
        if key in [ord('q'), ord('Q')]:
            break
        if key in [ord(x) for x in '0123456789']:
            print('changing to screen', chr(key))
        data = get_data(t=i/10) 
        for layer in screen['layers']:
            imshow_layer(data=data, layer=layer, window='main')
    print(i)

    
    # [ Sandbox ] Loop
    # Read camera
    # Send changes to [model]
    
    # [ Model ] Loop
    # Process updates
    # Timestep
    # Send data to [viz]
    
    # Finalize
    cv2.destroyAllWindows()
    
@click.command()
def main():
    ds = netCDF4.Dataset('models/Waal_schematic/DFM_OUTPUT_waal_with_side/waal_with_side_map.nc')
    viz = Visualization(ds)
    print(vars(viz))
    viz_loop()


    
if __name__ == '__main__':
    main()
