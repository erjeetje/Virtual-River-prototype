# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 09:56:24 2019

@author: HaanRJ
"""

import time
import json
import keyboard
import tygronInterface as tygron
import gridCalibration as cali
import processImage as detect
import gridMapping as gridmap
import updateFunctions as update


def mainmenu():
    start = True # boolean in order to only run initialize method once
    token = "" # empty string to store Tygron api session token
    d = 0 # turn tracker
    filename = 'board_image%d.jpg'%d  # snapshot filename
    hex_sandbox = None  # current hexagon state on the board, transformed to sandbox, geojson featurecollection (multipolygon)
    hex_sandbox_prev = None  # hex_sandbox state of previous update, geojson featurecollection (multipolygon)
    hex_tygron = None  # current hexagon state on the board, transformed to tygron (this may need to be changed to another transform), geojson featurecollection (multipolygon)
    hex_tygron_prev = None  # hex_tygron state of previous update, geojson featurecollection (multipolygon)
    hex_water = None  # current hexagons on the board that are water (z < 2), transformed to tygron, geojson featurecollection (multipolygon)
    hex_water_prev = None  # hex_water state of previous update, geojson featurecollection (multipolygon)
    hex_land = None  # current hexagon state on the board, transformed to tygron (this may need to be changed to), geojson featurecollection (multipolygon)
    hex_land_prev = None  # hex_land state of previous update, geojson featurecollection (multipolygon)
    transforms = None  # all necessary transforms
    grid = None  # sandbox grid, geojson featurecollection (points)
    grid_interpolated = None  # interpolated grid (with z), geojson featurecollection (points)
    print ("Virtual River started, press '5' to calibrate, press '1' to update and press '0' to quit")

    while(True):
        a = keyboard.read_key()
        if a == '5':
            if start:
                print("Calibrating Virtual River, preparing SandBox and logging into Tygron")
                """
                to add:
                - initiate camera
                - take new picture
                - send picture to initialize or store picture and send correct filename
                """
                token, hex_sandbox, hex_tygron, hex_water, hex_land, transforms = initialize(filename)
                with open('token.txt', 'w') as f:
                    f.write(token)
                hex_sandbox_prev = hex_sandbox
                hex_tygron_prev = hex_tygron
                hex_water_prev = hex_water
                hex_land_prev = hex_land
                grid = gridmap.read_grid()
                grid_interpolated = gridmap.hex_to_points(hex_sandbox, grid)
                """
                this section will also need scripts to:
                - to create the grid for sandbox
                - to store indices and weighing factors for interpolation
                - to execute the interpolation
                - to convert the grid to geotiff
                - to initialize all the changes in Tygron (water/land/buildings)
                - to initiate the hydrodynamic model
                - 
                """
                start = False
                print("Initializing complete")
            else:
                print("Already running")
                pass
                #print("Option {} was pressed\n".format(a))
        elif a == '1':
            print("Updating board state")
            d += 1
            filename = 'board_image%d.jpg'%d # snapshot filename
            print("Turn "+str(d))
        elif a == '0':
            print("Exiting\n")
            time.sleep(1)
            exit(0)
            break
        else:
            print("Unrecognized keystroke\n")
            exit(0)
        time.sleep(0.3)


def initialize(filename):
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    token = "token=" + tygron.join_session(username, password)
    canvas, thresh = cali.detectCorners(filename, method='adaptive')  # image name for calibration (would be first image pre-session)
    pers, img_x, img_y, origins, radius, cut_points, features = cali.rotateGrid(canvas, thresh)  # store calibration values as global variables
    transforms = cali.createCalibrationFile(img_x, img_y, cut_points)
    hexagons = detect.detectMarkers(filename, pers, img_x, img_y, origins, radius, features)
    hexagons_sandbox = detect.transform(hexagons, transforms, export="sandbox")
    hexagons_tygron = detect.transform(hexagons, transforms, export="tygron_initialize")
    hexagons_water, hexagons_land = detect.transform(hexagons, transforms, export="tygron")
    """
    with open('hexagons_features.json', 'w') as g:
        json.dump(features, g, sort_keys=True, indent=2)
    """
    return token, hexagons_sandbox, hexagons_tygron, hexagons_water, hexagons_land, transforms
    
    
def update():
    
    return


def compareHex(hexagons_new, hexagons_old):
    
    return


if __name__ == '__main__':
    mainmenu()