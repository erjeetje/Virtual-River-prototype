# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 09:56:24 2019

@author: HaanRJ
"""

import time
import geojson
import keyboard
import os
import tygronInterface as tygron
import gridCalibration as cali
import processImage as detect
import gridMapping as gridmap
import updateFunctions as compare
import webcamControl as webcam
import modelInterface as D3D
import updateRoughness as roughness
import createStructures as structures
from copy import deepcopy
#import plotHexagons as plotter


def main_menu():
    """
    Main script that continues to run during a session. Initiates the
    calibration and any updates thereafter. Stores all data while running
    """
    # path to save files
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path, 'storing_files')
    try:
        os.mkdir(dir_path)
        print("Directory ", dir_path, " Created.")
    except FileExistsError:
        print("Directory ", dir_path, " already exists, overwriting files.")
    # boolean in order to only run initialize method once
    start = True
    # empty string to store Tygron api session token
    token = ""
    # turn tracker
    turn = 0

    model = None

    hexagons_new = None

    hexagons_old = None
    # current hexagon state on the board, transformed to sandbox, geojson
    # featurecollection (multipolygon)
    hex_sandbox = None
    # hex_sandbox state of previous update, geojson featurecollection
    # (multipolygon)
    hex_sandbox_new = None
    # current hexagon state on the board, transformed to tygron (this may
    # need to be changed to another transform), geojson featurecollection
    # (multipolygon)
    hex_tygron = None
    # hex_tygron state of previous update, geojson featurecollection
    # (multipolygon)
    hex_tygron_new = None
    # current hexagons on the board that are water (z < 2), transformed to
    # tygron, geojson featurecollection (multipolygon)
    hex_water = None
    # hex_water state of previous update, geojson featurecollection
    # (multipolygon)
    hex_water_new = None
    # current hexagon state on the board, transformed to tygron (this may need
    # to be changed to), geojson featurecollection (multipolygon)
    hex_land = None
    # hex_land state of previous update, geojson featurecollection
    # (multipolygon)
    hex_land_new = None
    # all necessary transforms
    transforms = None
    # sandbox grid, geojson featurecollection (points)
    node_grid = None
    # interpolated grid (with z), geojson featurecollection (points)
    #grid_interpolated = None

    # filled board where hexagons located behind the dike are filled up in
    # order to have a closed geometry for Delft3D
    hexagons_adjusted_sandbox = None

    # filled node grid that can be used by Delft3D
    filled_node_grid = None

    # face grid to deal with roughness
    face_grid = None
    
    # heightmap for Tygron
    heightmap = None
    
    pers = None
    
    img_x = None
    
    img_y = None
    
    origins = None
    
    radius = None
    print("Virtual River started, press '5' to calibrate, "
          "press '1' to update and press '0' to quit")
    while(True):
        a = keyboard.read_key()
        if a == '5':
            if start:
                print("Calibrating Virtual River, preparing SandBox "
                      "and logging into Tygron")
                #try:
                token, hexagons_new, hex_sandbox, hex_tygron_int, hex_tygron, \
                    node_grid, filled_node_grid, face_grid, transforms, pers, \
                    img_x, img_y, origins, radius, model, heightmap, \
                    heightmap_id = initialize(turn, dir_path)
                #except TypeError:
                    #print("Calibration failed, closing application")
                    #time.sleep(2)
                    #break
                with open(os.path.join(dir_path, 'token.txt'), 'w') as f:
                    f.write(token)
                start = False
                print("Initializing complete, waiting for next command")
            else:
                print("Already running")
                pass
        elif a == '1':
            if not start:
                turn += 1
                hexagons_new, node_grid, filled_node_grid, face_grid, \
                    heightmap = update(token, dir_path, transforms, pers,
                                       img_x, img_y, origins, radius,
                                       hexagons_new, node_grid,
                                       filled_node_grid, face_grid,
                                       model, turn=turn)
                print("Update complete, waiting for next command")
            else:
                print("No calibration run, please first calibrate Virtual "
                      "River by pressing '5'")
                pass
        elif a == '0':
            print("Exiting\n")
            time.sleep(1)
            exit(0)
            break
        else:
            print("Unrecognized keystroke\n")
            exit(0)
        time.sleep(0.3)


def initialize(turn, dir_path, save=True):
    """
    Function that handles all the startup necessities:
    - calls logging into Tygron
    - initiates and calibrates the camera
    - get, perform and store the necessary transforms
    - process initial board state
    - initiate sandbox model
    - run sandbox model
    - update Tygron
    - return all variables that need storing
    """
    tic = time.time()
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    token = tygron.join_session(username, password)
    if token is None:
        print("logging in to Tygron failed, unable to make changes in Tygron")
    else:
        token = "token=" + token
        print("logged in to Tygron")
        img = webcam.get_image(turn, mirror=True)
        print("retrieved initial board image")
        # camera calibration --> to do: initiation
        # changed filename as variable to img
        canvas, thresh = cali.detect_corners(img, method='adaptive',
                                             path=dir_path)
        # store calibration values as global variables
        pers, img_x, img_y, origins, radius, cut_points, features \
            = cali.rotate_grid(canvas, thresh)
        # create the calibration file for use by other methods and store it
        transforms = cali.create_calibration_file(img_x, img_y, cut_points,
                                                  path=dir_path)
        print("calibrated camera")
        hexagons = detect.detect_markers(img, pers, img_x, img_y,
                                         origins, radius, features,
                                         method='LAB', path=dir_path)
        print("processed initial board state")
        hexagons = tygron.update_hexagons_tygron_id(token, hexagons)
        hexagons_sandbox = detect.transform(hexagons, transforms,
                                            export="sandbox", path=dir_path)
        hexagons_sandbox = structures.determine_dikes(hexagons_sandbox)
        hexagons_sandbox = structures.determine_channel(hexagons_sandbox)
        north_channel = structures.get_channel(hexagons_sandbox, north_side=True)
        south_channel = structures.get_channel(hexagons_sandbox, north_side=False)
        groynes_north = structures.create_groynes(north_channel,
                                                  north_side=True)
        groynes_south = structures.create_groynes(south_channel,
                                                  north_side=False)
        ltd_features_north = structures.create_LTDs(north_channel,
                                                    north_side=True)
        ltd_features_south = structures.create_LTDs(south_channel,
                                                    north_side=False)
        groynes_north_tygron = detect.transform(groynes_north, transforms,
                                               export="sandbox2tygron")
        groynes_south_tygron = detect.transform(groynes_south, transforms,
                                               export="sandbox2tygron")
        ltd_features_north_tygron = detect.transform(ltd_features_north,
                                                     transforms,
                                                     export="sandbox2tygron")
        ltd_features_south_tygron = detect.transform(ltd_features_south,
                                                     transforms,
                                                     export="sandbox2tygron")
        if True:
            with open('groynes_test_north_tygron.geojson', 'w') as f:
                geojson.dump(groynes_north_tygron, f, sort_keys=True, indent=2)
            with open('groynes_test_south_tygron.geojson', 'w') as f:
                geojson.dump(groynes_south_tygron, f, sort_keys=True, indent=2)
        if save:
            with open(os.path.join(dir_path, 'hexagons%d.geojson' % turn),
                      'w') as f:
                geojson.dump(hexagons_sandbox, f, sort_keys=True,
                             indent=2)
            print("saved hexagon file (conditional)")
        hexagons_tygron_int = detect.transform(hexagons, transforms,
                                               export="tygron_initialize")
        if save:
            with open(os.path.join(dir_path,
                                   'hexagons_tygron_initialization%d.geojson'
                                   % turn), 'w') as f:
                geojson.dump(hexagons_tygron_int, f, sort_keys=True,
                             indent=2)
            print("saved hexagon file (conditional)")
        hexagons_tygron = detect.transform(hexagons, transforms,
                                           export="tygron")
        print("prepared geojson files")
        model = D3D.initialize_model()
        node_grid = gridmap.read_node_grid(path=dir_path)
        face_grid = gridmap.read_face_grid(model, path=dir_path)
        print("loaded grid")
        node_grid = gridmap.index_node_grid(hexagons_sandbox, node_grid)
        face_grid = gridmap.index_face_grid(hexagons_sandbox, face_grid)
        node_grid = gridmap.interpolate_node_grid(hexagons_sandbox, node_grid,
                                                  turn=turn, path=dir_path)
        hexagons_sandbox, face_grid = roughness.hex_to_points(model,
                                                              hexagons_sandbox,
                                                              face_grid)
        print("executed grid interpolation")
        filled_node_grid = deepcopy(node_grid)
        filled_hexagons = deepcopy(hexagons_sandbox)
        filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
        filled_node_grid = gridmap.update_node_grid(filled_hexagons,
                                                    filled_node_grid,
                                                    fill=True)
        filled_node_grid = gridmap.interpolate_node_grid(filled_hexagons,
                                                         filled_node_grid,
                                                         turn=turn,
                                                         path=dir_path)
        if save:
            with open(os.path.join(dir_path, 'node_grid%d.geojson' % turn),
                      'w') as f:
                geojson.dump(node_grid, f, sort_keys=True,
                             indent=2)
            with open(os.path.join(dir_path,
                                   'filled_node_grid%d.geojson' % turn),
                      'w') as f:
                geojson.dump(filled_node_grid, f, sort_keys=True,
                             indent=2)
            print("saved interpolation files (conditional)")
        print("executed grid fill interpolation")
        heightmap = gridmap.create_geotiff(node_grid, turn=turn, path=dir_path)
        print("created geotiff")
        """
        This section is not very efficient, once the system is up and running
        replace this to either also check which hexagons need to change or make
        an empty project area that is either land or water only.
        """
        hexagons_tygron = tygron.set_terrain_type(token, hexagons_tygron)
        tygron.hex_to_terrain(token, hexagons)
        file_location = (dir_path + "\\grid_height_map" + str(turn) + ".tif")
        heightmap_id = tygron.set_elevation(file_location, token, turn=0)
        print("updated Tygron")
        print("stored initial board state")
        toc = time.time()
        print("Start up and calibration time: "+str(toc-tic))
    try:
        return token, hexagons, hexagons_sandbox, hexagons_tygron_int, \
            hexagons_tygron, node_grid, filled_node_grid, \
            face_grid, transforms, pers, img_x, img_y, origins, radius, \
            model, heightmap, heightmap_id
    except UnboundLocalError:
        print("logging in to Tygron failed, closing application")
        quit()


def update(token, dir_path, transforms, pers, img_x, img_y, origins, radius,
           hexagons_new, node_grid, filled_node_grid, face_grid, model, turn=1,
           save=True):
    """
    function that initiates and handles all update steps. Returns all update
    variables
    """
    tic = time.time()
    print("Updating board state")
    img = webcam.get_image(turn, mirror=True)
    print("retrieved board image after turn " + str(turn))
    hexagons_old = deepcopy(hexagons_new)
    hexagons_new = detect.detect_markers(img, pers, img_x, img_y, origins,
                                         radius, hexagons_new, turn=turn,
                                         method='LAB', path=dir_path)
    print("processed current board state")
    # this next update should not be necessary if tygron IDs are
    # properly updated at an earlier stage
    hexagons_new = tygron.update_hexagons_tygron_id(token, hexagons_new)
    hexagons_new, dike_moved = compare.compare_hex(token, hexagons_old,
                                                   hexagons_new)
    if dike_moved:
        hexagons_new = structures.determine_dikes(hexagons_new)
    hexagons_sandbox = detect.transform(hexagons_new, transforms,
                                        export="sandbox")
    hexagons_sandbox, face_grid = roughness.hex_to_points(model,
                                                          hexagons_sandbox,
                                                          face_grid)
    if save:
        with open(os.path.join(dir_path, 'hexagons%d.geojson' % turn),
                  'w') as f:
            geojson.dump(hexagons_sandbox, f, sort_keys=True,
                         indent=2)
        print("saved hexagon file for turn " + str(turn) + " (conditional)")
    hexagons_tygron = detect.transform(hexagons_new, transforms,
                                       export="tygron")
    hexagons_to_water, hexagons_to_land = compare.terrain_updates(
            hexagons_tygron)
    tygron.set_terrain_type(token, hexagons_to_water, terrain_type="water")
    tygron.set_terrain_type(token, hexagons_to_land, terrain_type="land")
    tygron.hex_to_terrain(token, hexagons_tygron)
    tac = time.time()
    node_grid = gridmap.update_node_grid(hexagons_sandbox, node_grid,
                                         turn=turn)
    node_grid = gridmap.interpolate_node_grid(hexagons_sandbox, node_grid,
                                              turn=turn, save=False,
                                              path=dir_path)
    """
    face grid update call should be added here. In addition, all geojson
    changed parameters should be changed to z_changed and landuse_changed
    """
    if dike_moved:
        filled_hexagons = deepcopy(hexagons_sandbox)
        filled_node_grid = deepcopy(node_grid)
        filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
        filled_node_grid = gridmap.update_node_grid(
                filled_hexagons, filled_node_grid, fill=True)
        filled_node_grid = gridmap.interpolate_node_grid(
                filled_hexagons, filled_node_grid, turn=turn, save=False,
                path=dir_path)
        print("updated complete grid, dike relocation detected")
    else:
        filled_node_grid = gridmap.update_node_grid(
                hexagons_sandbox, filled_node_grid, turn=turn)
        filled_node_grid = gridmap.interpolate_node_grid(
                hexagons_sandbox, filled_node_grid, turn=turn, save=False,
                path=dir_path)
    heightmap = gridmap.create_geotiff(node_grid, turn=turn, path=dir_path)
    file_location = (dir_path + "\\grid_height_map" + str(turn) + ".tif")
    heightmap_id = tygron.set_elevation(file_location, token, turn=0)
    if save:
        with open(os.path.join(dir_path, 'node_grid%d.geojson' % turn),
                  'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open(os.path.join(dir_path, 'filled_node_grid%d.geojson' % turn),
                  'w') as f:
            geojson.dump(filled_node_grid, f, sort_keys=True,
                         indent=2)
        print("saved grid files for turn " + str(turn) + " (conditional)")
    toc = time.time()
    print("Updated to turn " + str(turn) +
          ". Comparison update time: " + str(tac-tic) +
          ". Interpolation update time: " + str(toc-tac) +
          ". Total update time: " + str(toc-tic))
    return hexagons_new, node_grid, filled_node_grid, face_grid, heightmap


if __name__ == '__main__':
    main_menu()
