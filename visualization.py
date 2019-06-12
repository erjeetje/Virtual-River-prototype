import time
import json
import itertools

import click
import cv2

import numpy as np
import matplotlib.cm
import matplotlib.colors


def get_data(t=0, nx=500, ny=300):
    """generate some initial data"""
    # TODO: get this from the model
    def z_func(x, y, t):
        result = np.sin(t) * x  + np.cos(t) * y
        return result
    x = np.linspace(-3.0, 3.0, num=nx)
    y = np.linspace(-3.0, 3.0, num=ny)
    X,Y = np.meshgrid(x, y) # grid of point
    Z = z_func(X, Y, t=t) # evaluation of the function on the grid
    return {
        'zs': Z
    }

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
    viz_loop()


    
if __name__ == '__main__':
    main()
