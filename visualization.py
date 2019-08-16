import os
import time
import json
import itertools
import logging
import functools

import click
import cv2
import tqdm

import numpy as np
import matplotlib.cm
import matplotlib.colors
import netCDF4
import scipy.spatial
import skimage

import modelInterface as D3D

from models import available
from physics import warp_flow

logger = logging.getLogger(__name__)

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


def blend_transparent(background_img, overlay_img):
    """blend 2 transparent images"""

    # TODO: this is now very slow..., optimize
    # Perhaps check Pillow's alpha composite
    # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.alpha_composite
    
    # from: https://stackoverflow.com/questions/36921496/how-to-join-png-with-alpha-transparency-in-a-frame-in-realtime/37198079#37198079

    # If overlay img is without alfa, return it
    if overlay_img.shape[2] == 3:
        return overlay_img
    
    # Split out the transparency mask from the colour info
    overlay_bgr = overlay_img[:,:,:3] # Grab the BRG planes
    overlay_mask = overlay_img[:,:,3:]  # And the alpha plane

    # Again calculate the inverse mask
    background_mask = 255 - overlay_mask

    # Turn the masks into three channel, so we can use them as weights
    overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

    # Create a masked out background image, and masked out overlay
    # We convert the images to floating point in range 0.0 - 1.0
    background_part = ((background_img * (1 / 255.0)) *
                       (background_mask * (1 / 255.0)))
    overlay_part = ((overlay_bgr * (1 / 255.0)) *
                    (overlay_mask * (1 / 255.0)))

    # And finally just add them together, and rescale it back to an 8bit
    # integer image    
    return np.uint8(cv2.addWeighted(background_part, 255.0, overlay_part,
                                    255.0, 0.0))


class Visualization():
    def __init__(self, model, ds=None):
        if ds is None:
            self.ds = self.get_ds()
        else:
            self.ds = ds
        self.D3D = model
        
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

        """
        self.model = np.array([
            [-600, -400],
            [600, -400],
            [600, 400],
            [-600, 400]
        ], dtype='float32')
        """
        self.model = np.array([
            [-400, -300],
            [400, -300],
            [400, 300],
            [-400, 300]
        ], dtype='float32')

        self.transforms = self.compute_transforms()
        self.update_initial_vars(model=self.D3D, engine='live')
        self.grid = self.init_grid()
        self.init_screens()
        
    def read_config(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        screens_path = os.path.join(dir_path, 'screens.json')
        with open(screens_path) as f:
            config = json.load(f)
        return config

    def get_ds(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        nc_path = os.path.join(dir_path, 'models', 'Waal_schematic',
                               'DFM_OUTPUT_Virtual_River',
                               'Virtual_River_map.nc')
        ds = netCDF4.Dataset(nc_path)
        return ds

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
        meta = {
                "initial_vars": [
                        'xzw',
                        'yzw',
                        'xk',
                        'yk',
                        'zk',
                        'ndx',
                        'ndxi',  # number of internal points (no boundaries)
                        'flowelemnode',
                        'ln',
                        'frcu'
                        ],
                "vars": ['bl', 'ucx', 'ucy', 's1', 'zk', 'frcu'],
                "mapping": dict(
                        X_NODES="xk",
                        Y_NODES="yk",
                        X_CELLS="xzw",
                        Y_CELLS="yzw",
                        HEIGHT_NODES="zk",
                        HEIGHT_CELLS="bl",
                        WATERLEVEL="s1",
                        U="ucx",
                        V="ucy",
                        FLOW_LINKS='ln',
                        ROUGHNESS='frcu'
                ), }
        for name in meta['initial_vars']:
            if engine.endswith('_nc'):
                self.data[name] = self.ds.variables[name][:]
            else:
                self.data[name] = model.model.get_var(name)

        for name in meta['vars']:
            if engine.endswith('_nc'):
                self.data[name] = self.ds.variables[name][:]
            else:
                self.data[name] = model.model.get_var(name)
                self.data[name + '_0'] = model.model.get_var(name).copy()
        #meta['compute'](data)
        self.dflowfm_compute()
        for key, val in meta["mapping"].items():
            self.data[key] = self.data[val]
        self.data['FLOW'] = np.sqrt((self.data['U'])**2 + (self.data['V'])**2)
        self.data['WATERDEPTH'] = (self.data['WATERLEVEL'] -
                 self.data['HEIGHT_CELLS'])
        return


    def update_vars(self, model=None, engine='dflowfm_nc', t=0):
        """
        get the variables from the model and put them in the data dictionary
        """
        meta = {
                "initial_vars": [
                        'xzw',
                        'yzw',
                        'xk',
                        'yk',
                        'zk',
                        'ndx',
                        'ndxi',  # number of internal points (no boundaries)
                        'flowelemnode',
                        'ln',
                        'frcu'
                        ],
                "vars": ['bl', 'ucx', 'ucy', 's1', 'zk', 'frcu'],
                "mapping": dict(
                        X_NODES="xk",
                        Y_NODES="yk",
                        X_CELLS="xzw",
                        Y_CELLS="yzw",
                        HEIGHT_NODES="zk",
                        HEIGHT_CELLS="bl",
                        WATERLEVEL="s1",
                        U="ucx",
                        V="ucy",
                        FLOW_LINKS='ln',
                        ROUGHNESS='frcu'
                ), }
        for name in meta['vars']:
            if engine.endswith('_nc'):
                # start looping from the start
                t = (t % self.data['time'].shape[0])
                self.data[name] = self.ds.variables[name][t]
                self.data['t'] = self.data['time'][t]
            else:
                self.data[name] = model.model.get_var(name)
                self.data['t'] = "{:2f}".format(model.model.get_current_time())
        # do some stuff per model
        #meta["compute"](self.data)
        self.dflowfm_compute()
        for key, val in meta["mapping"].items():
            self.data[key] = self.data[val]
        self.data['FLOW'] = np.sqrt((self.data['U'])**2 + (self.data['V'])**2)
        self.data['WATERDEPTH'] = (self.data['WATERLEVEL'] -
                 self.data['HEIGHT_CELLS'])
    
    
    def add_image(self, key, data):
        self.data[key] = data
        return


    def dflowfm_compute(self):
        """
        compute variables that are missing/buggy/not available
        """
        numk = self.data['zk'].shape[0]
        self.data['numk'] = numk
        # fix shapes
        dflowfm_vars = ['bl', 'ucx', 'ucy', 's1', 'zk', 'frcu']
        for var_name in dflowfm_vars:
            arr = self.data[var_name]
            #print(var_name)
            #print(arr)
            if arr.shape[0] == self.data['numk']:
                self.data[var_name] = arr[:self.data['numk']]
            elif arr.shape[0] == self.data['ndx']:
                "should be of shape ndx"
                # ndxi:ndx are the boundary points
                # (See  netcdf write code in unstruc)
                self.data[var_name] = arr[:self.data['ndxi']]
                # data should be off consistent shape now
            elif arr.shape[0] == self.data['ndxi']:
                # this is ok
                pass
            elif arr.shape[0] == self.data['ln'].shape[0]:
                # this is ok
                pass
            else:
                msg = "unexpected data shape %s for variable %s" % (
                    arr.shape,
                    var_name
                    )
                raise ValueError(msg)
        # compute derivitave variables, should be consistent shape now.
        #self.data['is_wet'] = self.data['s1'] > self.data['bl']
        return


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

        flow_links = self.data['FLOW_LINKS']
        """
        link_grid = [[cell_centers[links[0]][0]+cell_centers[links[1]][0],
                      cell_centers[links[0]][1]+cell_centers[links[1]][1]]
                     for links in flow_links]
        """
        
        link_grid = []
        for link in flow_links:
            try:
                cell1 = cell_centers[link[0]-1]
                cell2 = cell_centers[link[1]-1]
                flow_x = (cell1[0] + cell2[0]) / 2.0
                flow_y = (cell1[1] + cell2[1]) / 2.0
                link_grid.append([flow_x, flow_y])
            except IndexError:
                continue
        link_grid = np.array(link_grid)
        tree = scipy.spatial.cKDTree(link_grid)
        distances_links, ravensburger_links = tree.query(np.c_[m_t, n_t])
        data['ravensburger_links'] = ravensburger_links.reshape(HEIGHT, WIDTH)
        data['distances_links'] = distances_links.reshape(HEIGHT, WIDTH)
        
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
        #cv2.namedWindow('debug', flags=cv2.WINDOW_OPENGL | cv2.WINDOW_NORMAL)
        cv2.namedWindow('debug', flags=cv2.WINDOW_NORMAL)
        # Create a main window for the beamer
        #cv2.namedWindow('main', flags=cv2.WINDOW_OPENGL | cv2.WINDOW_NORMAL)
        cv2.namedWindow('main', flags=cv2.WINDOW_NORMAL)
        # make main window full screen
        if self.config['settings'].get('fullscreen', False):
            cv2.moveWindow('main', -1920, -1080)
            cv2.setWindowProperty('main', cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN)


    def set_screen(self, key):
        for screen in self.config['screens']:
            if screen['key'] == key:
                self.screen = screen
                break
        else:
            logger.warn('screen %s not available', key)


    def put_text(self, text, window='debug'):
        WIDTH = self.config['settings']['width']
        HEIGHT = self.config['settings']['height']
        img = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (255, 255, 255)
        
        scale = 1
        for i, line in enumerate(text.split('\n')):
            origin = (50, 50 + i * 50)
            cv2.putText(img, line, origin, font, scale, color)
        return img


    def image(self, layer):
        rgb = self.data[layer['variable']]
        if layer['blur'] is True:
            kernel = (15, 15)
            rgb = cv2.GaussianBlur(rgb, kernel, cv2.BORDER_DEFAULT)
        return rgb


    def imshow(self, layer):
        # get the variable for this layer
        var = self.data[layer['variable']]
        # get min and max if set
        min_value = min(var)
        max_value = max(var)

        # the normalization function
        N = matplotlib.colors.Normalize(min_value, max_value)
        # the colormap
        cmap = getattr(matplotlib.cm, layer['colormap'])

        # The gridded image
        if layer['grid'] == "CELLS":
            arr = var[self.grid['ravensburger_cells']]
        elif layer['grid'] == "NODES":
            arr = var[self.grid['ravensburger_nodes']]
        elif layer['grid'] == "LINKS":
            arr = var[self.grid['ravensburger_links']]
        else:
            msg = "variable has an unspecified or unknown grid"
            raise ValueError(msg)

        # the colored image
        rgba = cmap(N(arr))
        
        # add a blur in case layer asks for it
        if layer['blur'] is True:
            kernel = (15, 15)
            rgba = cv2.GaussianBlur(rgba, kernel, cv2.BORDER_DEFAULT)

        # TODO: check if we can do this with opencv (convert or something...)
        #rgb = np.uint8(rgba * 256)[...,:3]
        rgb = np.uint8(rgba * 255)[...,:3]

        # this is one plot, other variants might include advection of colors 
        return rgb


    def seed_lic(self, layer):
        
        # Put in new white dots (to be plotted next time step)
        n_dots = 4
        size = 4
        WIDTH = self.config['settings']['width']
        HEIGHT = self.config['settings']['height']

        coords = np.random.random((n_dots, 2)) * (HEIGHT, WIDTH)

        if not 'lic' in self.data:
            self.data['lic'] = np.zeros((HEIGHT, WIDTH, 4))

        for x, y in coords:
            # white
            ref = self.grid['ravensburger_cells'][int(x), int(y)]
            """ 
            # only seed lics where water levels are high
            water_level = self.data['s1'][ref] - self.data['bl'][ref]
            if (water_level < 7.5):
                continue
            """
            # only seed lics where there is at least some water flow
            flow = self.data['FLOW'][ref]
            if (flow < 0.25):
                continue
            #color = (1, 1, 1)
            
            # make sure outline has the same color
            # create a little dot
            #r, c = skimage.draw.circle(y, x, size, shape=(HEIGHT, WIDTH))
            r, c = skimage.draw.circle(x, y, size, shape=(WIDTH, HEIGHT))
            self.data['lic'][r, c] = 1


    def lic(self, layer):

        scale = layer['scale']

        # get the u,v vectors
        u = self.data['U']
        v = self.data['V']

        # transform to matrices
        U = u[self.grid['ravensburger_cells']]
        V = v[self.grid['ravensburger_cells']]

        # create an image to transform
        self.seed_lic(layer)

        flow = np.dstack([U, V]) * scale

        self.data['lic'] = warp_flow(
            self.data['lic'].astype('float32'),
            flow.astype('float32')
        )

        #return (self.data['lic'] * 256).astype('uint8')
        return (self.data['lic'] * 255).astype('uint8')


    def loop(self):
        for i in tqdm.tqdm(itertools.count()):

            # Process key input
            key = cv2.waitKey(1)
            # quit
            if key in [ord('q'), ord('Q')]:
                break
            # switch screen
            if key in [ord(x) for x in '0123456789']:
                # key is a number, convert to corresponding letter
                self.set_screen(chr(key))

            # Process input
            # You could process camera input here

            # Model updates
            # You could update the model here

            # Update the variables
            self.update_vars(t=i, model=self.D3D, engine='live')

            # Nowe we can render
            rgbas = []
            for layer in self.screen['layers']:
                # We are rendering in RGBA
                if layer['type'] == 'imshow':
                    rgba = self.imshow(layer=layer)
                if layer['type'] == 'lic':
                    rgba = self.lic(layer)
                if layer['type'] == 'image':
                    rgba = self.image(layer)
                rgbas.append(rgba)
                
            # merge the layers (can perhaps be done faster)
            rgba = functools.reduce(blend_transparent, rgbas)

            
            # Open CV expects BGR, never found out why
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            bgr = cv2.flip(bgr, 1)
            cv2.imshow('main', bgr)

            img =  self.put_text('Timestep: %s\nT: %s' % (i, self.data['t']))
            cv2.imshow('debug', img)


    def close(self):
        # Finalize
        cv2.destroyAllWindows()


    def __del__(self):
        self.close()


@click.command()
def main():
    logging.basicConfig(level=logging.DEBUG)
    model = D3D.Model()
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #nc_path = os.path.join(dir_path, 'models', 'Waal_schematic',
    #                       'DFM_OUTPUT_Virtual_River', 'Virtual_River_map.nc')
    #ds = netCDF4.Dataset(nc_path)
    viz = Visualization(model)
    viz.loop()
    viz.close()


    
if __name__ == '__main__':
    main()
