# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:35:25 2019

@author: HaanRJ
"""

import sys
import time
import geojson
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
import costModule as costs
import waterModule as water
import indicatorModule_IHE as indicator
import ghostCells as ghosts
import hexagonAdjustments as adjust
import hexagonOwnership as owner
import visualization as visualize
from copy import deepcopy
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QCoreApplication


class GUI(QWidget):
    def __init__(self):
        super(GUI, self).__init__()
        self.initUI()

    def initUI(self):
        self.script = runScript()
        btn_update = QPushButton('Update', self)
        btn_update.clicked.connect(self.on_update_button_clicked)
        btn_update.resize(180, 40)
        btn_update.move(20, 35)
        btn_initialize = QPushButton('Initialize', self)
        btn_initialize.clicked.connect(self.on_initialize_button_clicked)
        btn_initialize.resize(180, 40)
        btn_initialize.move(20, 80)
        btn_model = QPushButton('Run model', self)
        btn_model.clicked.connect(self.on_model_button_clicked)
        btn_model.resize(180, 40)
        btn_model.move(20, 170)
        btn_exit = QPushButton('Exit', self)
        btn_exit.clicked.connect(self.on_exit_button_clicked)
        btn_exit.resize(180, 40)
        btn_exit.move(20, 260)
        """
        # incorporated the score updates within the other script functions,
        # called and update automatically.
        btn_scores = QPushButton('Show scores', self)
        btn_scores.clicked.connect(self.on_score_button_clicked)
        btn_scores.resize(180, 40)
        btn_scores.move(280, 35)
        """
        btn_round = QPushButton('End round', self)
        btn_round.clicked.connect(self.on_end_round_button_clicked)
        btn_round.resize(180, 40)
        btn_round.move(280, 80)
        btn_save = QPushButton('Save', self)
        btn_save.clicked.connect(self.on_save_button_clicked)
        btn_save.resize(180, 40)
        btn_save.move(280, 170)
        btn_reload = QPushButton('Reload', self)
        btn_reload.clicked.connect(self.on_reload_button_clicked)
        btn_reload.resize(180, 40)
        btn_reload.move(280, 260)
        self.setWindowTitle('Virtual River interface')
        self.show()  # app.exec_()

    def on_update_button_clicked(self):
        print("Calling update function")
        self.script.update()

    def on_initialize_button_clicked(self):
        print("Calling initialize function")
        self.script.initialize()
        
    def on_model_button_clicked(self):
        print("Calling model function")
        self.script.run_model()

    def on_exit_button_clicked(self):
        alert = QMessageBox()
        alert.setText('Exiting Virtual River')
        alert.exec_()
        QCoreApplication.instance().quit()
    
    def on_end_round_button_clicked(self):
        print("Calling end round function")
        self.script.end_round()
        
    def on_save_button_clicked(self):
        print("Calling save function")
        self.script.save_files()
        
    def on_reload_button_clicked(self):
        print("Calling reload function")
        self.script.reload()
        
    def on_score_button_clicked(self):
        print("Calling score function")
        self.script.scores()


class runScript():
    """
    
    """
    def __init__(self):
        super(runScript, self).__init__()
        # Defines and creates all the path locations used troughout the script.
        # In case changes were made to file locations (with this file as
        # the reference point), these need to be updated. 
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.store_path = os.path.join(self.dir_path, 'storing_files')
        try:
            os.mkdir(self.store_path)
            print("Directory ", self.store_path, " Created.")
        except FileExistsError:
            print("Directory ", self.store_path,
                  " already exists, overwriting files.")
        self.processing_path = os.path.join(self.dir_path, 'processing_files')
        try:
            os.mkdir(self.processing_path)
            print("Directory ", self.processing_path, " Created.")
        except FileExistsError:
            print("Directory ", self.processing_path,
                  " already exists, overwriting files.")
        self.model_path = os.path.join(self.dir_path, 'models',
                                       'Waal_schematic')
        self.config_path = os.path.join(self.dir_path, 'config_files')
        self.test_path = os.path.join(self.dir_path, 'test_files')
        # the following variables are used to determine what functions the
        # script calls and which it skips. The variables are automatically
        # update in the initialization depending on whether or not a camera
        # is detected and a tygron session is found.
        self.initialized = False
        self.reload_enabled = False
        self.start_new_turn = False
        self.test = False
        self.tygron = True
        self.ghost_hexagons_fixed = False
        # save variables, adjust as you wish how to run Virtual River
        self.save = False
        self.model_save = False
        self.model_ini_save = False
        # Virtual River variables. THESE ARE ADJUSTABLE!
        self.slope = 10**-3  # tested and proposed range: 10**-3 to 10**-4
        self.vert_scale = 0.25  # setting matches current z scaling, testing.
        # Mixtype vegetation class ratio in % for natural grass/reed/brushwood
        # Currently not used, but can be passed to landuse_to_friction function
        # of the updateRoughness module.
        self.mixtype_ratio = [50, 20, 30]
        self.ini_loops = 12  # number of model loops to run on initialization
        self.update_loops = 5  # number of model loops to run on updates
        # Memory variables
        self.turn = 0
        self.token = ""
        self.model = D3D.Model()
        self.hexagons = None
        self.hexagons_sandbox = None
        self.hexagons_tygron = None
        self.hexagons_prev = None
        self.transforms = None
        self.node_grid = None
        self.node_grid_prev = None
        self.filled_node_grid = None
        self.filled_node_grid_prev = None
        self.flow_grid = None
        self.face_grid = None
        self.heightmap = None
        self.pers = None
        # may not be necessary to store these, but some methods would need to
        # be updated (in gridCalibration and processImage).
        self.img_x = None
        self.img_y = None
        self.origins = None
        self.radius = None
        # temporary variables in relation to colormap plots
        self.fig = None
        self.axes = None
        # water safety module
        self.indicators = indicator.Indicators()
        # cost module
        self.cost_module = costs.Costs()
        # total costs made up until the end of the rounds ended
        self.total_costs = 0
        # turn costs of the current round
        self.turn_costs = 0
        # BIOSAFE module
        # TODO
        # visualization
        self.viz = visualize.Visualization(self.model)
    
    
    def initialize(self):
        if self.initialized:
            print("Virtual River is already initialized, please use Update "
                  "instead.")
            return
        tic = time.time()
        with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
            username = f.read()
        with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
            password = g.read()
        api_key = tygron.join_session(username, password)
        if api_key is None:
            print("logging in to Tygron failed, running Virtual River without "
                  "Tygron")
            self.tygron = False
        else:
            self.token = "token=" + api_key
            print("logged in to Tygron")
        # get image from camera
        img = webcam.get_image(self.turn, mirror=True)
        print("Retrieved initial board image")
        # calibrate camera
        # try - except TypeError --> if nothing returned by method, then go to
        # test mode.
        try:
            canvas, thresh = cali.detect_corners(img, method='adaptive',
                                                 path=self.processing_path)
        except TypeError:
            self.test = True
            print("TEST MODE: No camera detected, entering test mode")
        # adjust image, get the hexagons and store calibration values as global
        # variables.
        if not self.test:
            self.pers, self.img_x, self.img_y, self.origins, self.radius, \
                cut_points, self.hexagons = cali.rotate_grid(canvas, thresh)
            print("Calibrated camera.")
            # create the calibration file for use by other methods and store it
            # change dir_path to config_path
            self.transforms = cali.create_calibration_file(
                    self.img_x, self.img_y, cut_points, path=self.config_path)
            
            # update the hexagons to initial board state.
            self.hexagons = detect.detect_markers(
                    img, self.pers, self.img_x, self.img_y, self.origins,
                    self.radius, self.hexagons, method='LAB', path=self.store_path)
            self.hexagons = ghosts.set_values(self.hexagons)
            print("Processed initial board state.")
        else:
            self.transforms = cali.create_calibration_file(
                    path=self.config_path, test = self.test)
        # update the tygron_ids of the hexagons. These must be updated to match
        # the hexagons to the correct hexagons in Tygron.
        
        # transform the hexagons to sandbox coordinates
        if not self.test:
            if self.tygron:
                self.hexagons = tygron.update_hexagons_tygron_id(self.token,
                                                                 self.hexagons)
            self.hexagons_sandbox = detect.transform(
                    self.hexagons, self.transforms, export="sandbox",
                    path=self.dir_path)
            self.hexagons_sandbox = adjust.add_bedslope(
                    self.hexagons_sandbox, self.slope)
            self.hexagons_sandbox = adjust.z_correction(
                    self.hexagons_sandbox, initialized=self.initialized)
        
            # detect where the main channel and dikes are located and construct
            # both the groynes and longitudinal training dams for the model.
        else:
            print("TEST MODE: Getting new board state from test folder.")
            self.hexagons_sandbox = gridmap.read_hexagons(
                    filename='hexagons%d.geojson' % self.turn,
                    path=self.test_path)
            self.hexagons_sandbox = ghosts.set_values(self.hexagons_sandbox)
            self.hexagons_sandbox = owner.determine_neighbours(
                    self.hexagons_sandbox)
            self.hexagons_sandbox = adjust.test_mode_z_correction(
                    self.hexagons_sandbox)
            #self.hexagons_sandbox = adjust.add_bedslope(
            #        self.hexagons_sandbox, self.slope)
            #self.hexagons_sandbox = adjust.z_correction(self.hexagons_sandbox)
            if self.tygron:
                self.hexagons_sandbox = tygron.update_hexagons_tygron_id(
                        self.token, self.hexagons_sandbox)
            print("Received current board state.")
        self.hexagons_sandbox = structures.determine_dikes(
                self.hexagons_sandbox)
        self.hexagons_sandbox = structures.determine_channel(
                self.hexagons_sandbox)
        self.hexagons_sandbox = structures.determine_floodplains_and_behind_dikes(
                self.hexagons_sandbox)
        self.hexagons_sandbox = owner.determine_neighbours(
                self.hexagons_sandbox)
        self.hexagons_sandbox = owner.generate_ownership(
                self.hexagons_sandbox)
        # turned ownership off for the IHE session! TURN IT BACK ON
        #self.hexagons_sandbox = owner.determine_ownership(
        #        self.hexagons_sandbox)
        self.hexagons_sandbox = adjust.find_factory(
                self.hexagons_sandbox)
        #channel = structures.get_channel(self.hexagons_sandbox)
        #weirs = structures.create_structures(channel)
        #D3D.geojson2pli(weirs)
        print("Created structure files (groynes and ltds).")
        """
        # doesn't work properly after changing the shapes to linestrings
        # instead of polygons --> to fix
        
            structures_tygron = detect.transform(weirs,
                                                 self.transforms,
                                                 export="sandbox2tygron")
        """
        if self.tygron:
            # transform the hexagons to tygron initialization coordinates -->
            # this may now be obsolete after the tygron LTS upgrade, transform
            # is the same, although correct CRS is still required.
            if not self.test:
                hexagons_tygron_int = detect.transform(
                        self.hexagons, self.transforms,
                        export="tygron_initialize")
                # transform hexagons to tygron coordinates.
                self.hexagons_tygron = detect.transform(
                        self.hexagons, self.transforms, export="tygron")
            else:
                self.hexagons_tygron = detect.transform(
                        self.hexagons_sandbox, self.transforms,
                        export="sandbox2tygron")
        print("Prepared and transformed geojson featurecollections.")
        # initialize Delft3D-FM model
        tac = time.time()
        #self.model = D3D.initialize_model()
        # get node grid (cell corner coordinates) and face grid (cell
        # center coordinates)
        self.node_grid = gridmap.read_node_grid(path=self.store_path)
        self.flow_grid = gridmap.create_flow_grid(self.model.model,
                                                  path=self.store_path)
        self.face_grid = gridmap.read_face_grid(self.model.model,
                                                path=self.store_path)
        print("Loaded grids (cell corners and cell centers).")
        # index both grids to the hexagons.
        self.node_grid = gridmap.index_node_grid(self.hexagons_sandbox,
                                                 self.node_grid, self.slope)
        self.flow_grid = gridmap.index_flow_grid(self.hexagons_sandbox,
                                                 self.flow_grid)
        self.hexagons_sandbox = gridmap.index_hexagons(self.hexagons_sandbox,
                                                       self.face_grid)
        # initiate the interpolation to get the initial elevation model.
        self.node_grid = gridmap.interpolate_node_grid(
                self.hexagons_sandbox, self.node_grid, turn=self.turn,
                fill=False, path=self.dir_path)
        # set the Chezy coefficient for each hexagon (based on water levels
        # and trachytopes) 
        self.hexagons_sandbox = self.model.update_waterlevel(self.hexagons_sandbox)
        self.hexagons_sandbox = roughness.landuse_to_friction(
                self.hexagons_sandbox, vert_scale=self.vert_scale,
                initialization=True)
        self.hexagons_sandbox, self.flow_grid = roughness.hex_to_points(
                self.model.model, self.hexagons_sandbox, self.flow_grid)
        print("Executed grid interpolation.")
        # create a deepcopy of the node grid and fill the grid behind the
        # dikes. The filled node grid is for the hydrodynamic model.
        self.filled_node_grid = deepcopy(self.node_grid)
        filled_hexagons = deepcopy(self.hexagons_sandbox)
        filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
        self.filled_node_grid = gridmap.update_node_grid(
                filled_hexagons, self.filled_node_grid, fill=True)
        self.filled_node_grid = gridmap.interpolate_node_grid(
                filled_hexagons, self.filled_node_grid, turn=self.turn,
                fill=True, path=self.dir_path)
        print("Executed grid fill interpolation.")
        tec = time.time()
        if self.tygron:
            # a geotiff of the node grid is required to set the elevation in
            # tygron.
            t0 = time.time()
            self.heightmap = gridmap.create_geotiff(
                self.node_grid, turn=self.turn, path=self.store_path)
            print("Created geotiff elevation map")
            self.hexagons_tygron = tygron.set_terrain_type(
                    self.token, self.hexagons_tygron)
            tygron.hex_to_terrain(self.token, self.hexagons_tygron)
            file_location = (self.store_path + "\\grid_height_map" +
                             str(self.turn) + ".tif")
            heightmap_id = tygron.set_elevation(
                    file_location, self.token, turn=self.turn)
            t1 = time.time()
            print("Updated Tygron world from current board state.")
        """
        # run the model. --> this is currently separate from the initialization
        # as the whole system becomes rather slow. Added a temporary run model
        # button to the Virtual River GUI to run the model instead.
        self.fig, self.axes = D3D.run_model(
                self.model, self.filled_node_grid, self.flow_grid,
                self.hexagons_sandbox, initialized=self.initialized)
        """
        """
        # Not sure it makes sense to store the structures ?
        with open(os.path.join(self.store_path,
                               'structures.geojson'), 'w') as f:
            geojson.dump(weirs, f, sort_keys=True,
                         indent=2)
        print("Saved structures file (conditional).")
        """
        # system is now initialized
        self.initialized = True
        self.scores()
        toc = time.time()
        try:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Tygron terrain update time: " +
                  str(round(t1-t0, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        #self.update_viz()
        return


    def update(self):
        """
        function that initiates and handles all update steps. Returns all update
        variables
        """
        if not self.initialized:
            print("ERROR: Virtual River is not yet calibrated, "
                  "please first run initialize")
            return
        if (self.initialized and self.turn == 0):
            print("ERROR: It seems Virtual River is initialized, but that end "
                  "end round has not yet been triggered.")
            return
        tic = time.time()
        print("Updating board state")
        #self.turn += 1
        # get new image of board state from camera.
        if not self.test:
            img = webcam.get_image(self.turn, mirror=True)
            print("Retrieved board image after turn " + str(self.turn) + ".")
            # create a deepcopy of the previous board state to compare with the new
            # board state.
            #self.hexagons_prev = deepcopy(self.hexagons)
            self.hexagons = detect.detect_markers(
                    img, self.pers, self.img_x, self.img_y, self.origins,
                    self.radius, self.hexagons, turn=self.turn, method='LAB',
                    path=self.store_path)
            self.hexagons = adjust.z_correction(self.hexagons)
            print("Processed current board state.")
            if self.tygron:
                # update hexagon ids to matching ids in tygron.
                self.hexagons = tygron.update_hexagons_tygron_id(
                        self.token, self.hexagons)
            # compare the new board state to the old board state. Sets 'z_changed'
            # and 'landuse_changed' to True or False accordingly. Also tracks if
            # either or both of the dike locations changed.
            self.hexagons, self.turn_costs, dike_moved = compare.compare_hex(
                    self.cost_module, self.hexagons_prev, self.hexagons)
            #self.total_costs = self.total_costs + turn_costs
            # transform the hexagons to the sandbox coordinates --> check if this
            # is necessary, as the main hexagons are already updated, they should
            # be linked in memory to the sandbox hexagons.
            self.hexagons_sandbox = detect.transform(
                    self.hexagons, self.transforms, export="sandbox")
            # THIS SHOULD BE MOVED TO INITIALIZE AFTER MODEL IS FIXED TO INITIALIZATION
            if not self.ghost_hexagons_fixed:
                self.hexagons_sandbox = ghosts.update_values(
                        self.hexagons_sandbox)
                self.ghost_hexagons_fixed = True
                print("Fixed the ghost cell values")
        else:
            #self.hexagons_prev = deepcopy(self.hexagons_sandbox)
            try:
                print("TEST MODE: Getting new board state from test folder.")
                self.hexagons_sandbox = gridmap.read_hexagons(
                        filename='hexagons%d.geojson' % self.turn,
                        path=self.test_path)
                self.hexagons_sandbox = ghosts.set_values(
                        self.hexagons_sandbox)
                self.hexagons_sandbox = adjust.test_mode_z_correction(
                    self.hexagons_sandbox)
                print("Received current board state.")
            except FileNotFoundError:
                print("ERROR: Ran out of test files, aborting update function."
                      " Please restart the application to continue testing.")
                return
            # THIS SHOULD BE MOVED TO INITIALIZE AFTER MODEL IS FIXED TO INITIALIZATION
            if not self.ghost_hexagons_fixed:
                self.hexagons_sandbox = ghosts.update_values(
                        self.hexagons_sandbox)
                self.ghost_hexagons_fixed = True
                print("Fixed the ghost cell values")
            if self.tygron:
                # update hexagon ids to matching ids in tygron.
                self.hexagons_sandbox = tygron.update_hexagons_tygron_id(
                        self.token, self.hexagons_sandbox)
            self.hexagons_sandbox, self.turn_costs, dike_moved = compare.compare_hex(
                    self.cost_module, self.hexagons_prev,
                    self.hexagons_sandbox)
            #self.total_costs = self.total_costs + turn_costs
        # update the Chezy coefficients of all hexagons.
        if self.test:
            self.hexagons_sandbox = self.model.update_waterlevel(self.hexagons_sandbox)
        self.hexagons_sandbox = roughness.landuse_to_friction(
                self.hexagons_sandbox, vert_scale=self.vert_scale)
        self.hexagons_sandbox, self.flow_grid = roughness.hex_to_points(
                self.model.model, self.hexagons_sandbox, self.flow_grid)

        tac = time.time()
        if self.tygron:
            # transform the hexagons to the sandbox coordinates --> check if this
            # is necessary, as the main hexagons are already updated, they should
            # be linked in memory to the sandbox hexagons.
            t0 = time.time()
            if not self.test:
                self.hexagons_tygron = detect.transform(
                        self.hexagons, self.transforms, export="tygron")
            else:
                self.hexagons_tygron = detect.transform(
                        self.hexagons_sandbox, self.transforms,
                        export="sandbox2tygron")
            # get the hexagons that should be changed to water or land in
            # tygron.
            #hexagons_to_water, hexagons_to_land = compare.terrain_updates(
            #        self.hexagons_tygron)
            # update tygron terrain
            tygron.set_terrain_type(
                    self.token, self.hexagons_tygron)
            tygron.hex_to_terrain(self.token, self.hexagons_tygron)
            t1 = time.time()

        tec = time.time()
        # set the 'changed' property of each node grid point to True or False
        # based on the comparison with the previous turn (only update what
        # needs to be updated).
        self.node_grid = gridmap.update_node_grid(
                self.hexagons_sandbox, self.node_grid, turn=self.turn,
                printing=True)
        # update the elevation model by only performing interpolation for the
        # points that have changed.
        self.node_grid = gridmap.interpolate_node_grid(
                self.hexagons_sandbox, self.node_grid, fill=False, 
                turn=self.turn, save=False, path=self.dir_path)
        if dike_moved:
            # if the dike locations changed, the filled node grid needs to be
            # rebuild as the filled hexagon locations are changed as well.
            self.hexagons_sandbox = structures.determine_dikes(
                self.hexagons_sandbox)
            self.hexagons_sandbox = structures.determine_floodplains_and_behind_dikes(
                self.hexagons_sandbox)
            filled_hexagons = deepcopy(self.hexagons_sandbox)
            filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
            self.filled_node_grid = deepcopy(self.node_grid)
            self.filled_node_grid = gridmap.update_node_grid(
                    filled_hexagons, self.filled_node_grid, fill=True)
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    filled_hexagons, self.filled_node_grid, turn=self.turn,
                    fill=True, save=False, path=self.dir_path)
            print("updated complete grid, dike relocation detected")
        else:
            # if the dike locations did not change, a simple update suffices.
            self.filled_node_grid = gridmap.update_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid,
                    turn=self.turn, grid_type="filled")
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid,
                    turn=self.turn, fill=True, save=False, path=self.dir_path)
        toc = time.time()
        if self.tygron:
            # create a new geotiff and set the new elevation in tygron.
            t2 = time.time()
            self.heightmap = gridmap.create_geotiff(
                    self.node_grid, turn=self.turn, path=self.store_path)
            file_location = (self.store_path + "\\grid_height_map" +
                             str(self.turn) + ".tif")
            heightmap_id = tygron.set_elevation(
                    file_location, self.token, turn=0)
            print("Updated Tygron heightmap.")
            t3 = time.time()
        """
        # run the model. --> this is currently separate from the initialization
        # as the whole system becomes rather slow. Added a temporary run model
        # button to the Virtual River GUI to run the model instead.
        self.fig, self.axes = D3D.run_model(
                    self.model, self.filled_node_grid, self.flow_grid,
                    self.hexagons_sandbox, initialized=self.initialized,
                    fig=self.fig, axes=self.axes)
        """
        self.scores()
        self.start_new_turn = False
        print("Turn costs: " + str(self.turn_costs) + ". Total costs: " +
              str(self.total_costs + self.turn_costs))
        try:
            print("Updated to turn " + str(self.turn) +
              ". Comparison update time: " + str(round(tac-tic, 2)) +
              " seconds. Interpolation update time: " +
              str(round(toc-tec, 2)) + " seconds. Tygron update time: " +
              str(round((t1-t0)+(t3-t2), 2)) +
              " seconds. Total update time: " + str(round(t3-tic, 2)) +
              " seconds.")
        except UnboundLocalError:
            print("Updated to turn " + str(self.turn) +
              ". Comparison update time: " + str(round(tac-tic, 2)) +
              " seconds. Interpolation update time: " +
              str(round(toc-tec, 2)) + " seconds. Total update time: " +
              str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return
    
    def run_model(self):
        """
        Temporary separate function to update and run the model. Called by
        clicking the run model button in the GUI
        """
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run initialize")
            return
        if self.turn == 0:
            print("Running model after initialization, updating the elevation "
                  "in the model will take some time. Running "+ str(self.ini_loops) +
                  " loops to stabilize.")
            self.model.set_indexes(self.filled_node_grid, self.face_grid)
            self.hexagons_sandbox, self.flow_grid = self.model.run_model(
                    self.filled_node_grid, self.hexagons_sandbox, self.flow_grid,
                    self.vert_scale, turn=self.turn)
            """
            self.model.run_model(grid, self.hexagons_sandbox,
                                 self.flow_grid, self.vert_scale,
                                 turn=self.turn)
            self.hexagons_sandbox = self.model.update_waterlevel(
                    self.hexagons_sandbox)
            self.hexagons_sandbox = roughness.landuse_to_friction(
                self.hexagons_sandbox, vert_scale=self.vert_scale)
            self.hexagons_sandbox, self.flow_grid = roughness.hex_to_points(
                self.model.model, self.hexagons_sandbox, self.flow_grid)
            """
            print("Finished running the model after initialization.")
            print("NOTE: If you are running tests, make sure to first press "
                  "'Update'. Otherwise the elevation in the model will be "
                  "updated again (which is slow).")
            if self.model_ini_save:
                with open(os.path.join(self.store_path,
                                       'flow_grid_model_ini%d.geojson' % self.turn),
                          'w') as f:
                    geojson.dump(self.flow_grid, f, sort_keys=True,
                                 indent=2)
                with open(os.path.join(self.store_path,
                                       'hexagons_model_ini%d.geojson' % self.turn),
                          'w') as f:
                    geojson.dump(
                            self.hexagons_sandbox, f, sort_keys=True, indent=2)
        else:
            print("Running model after turn update, running " +
                  str(self.update_loops) + " loops.")
            #for i in range(0, self.update_loops):
            self.hexagons_sandbox, self.flow_grid = self.model.run_model(
                    self.filled_node_grid, self.hexagons_sandbox, self.flow_grid,
                    self.vert_scale, turn=self.turn)
            print("Finished running the model after turn " + str(self.turn) +
                  ".")
        if self.model_save:
            with open(os.path.join(self.store_path,
                                   'hexagons_with_model_output%d.geojson' %
                                   self.turn),
                      'w') as f:
                geojson.dump(self.hexagons_sandbox, f, sort_keys=True,
                             indent=2)
            print("stored hexagon files with model output (conditional)")
        self.hexagons_sandbox = self.model.update_waterlevel(self.hexagons_sandbox)
        self.scores()
        self.update_viz()
        return
    
    
    def reload(self):
        if not self.reload_enabled:
            print("Are you sure you want to iniate a reload? If you intended "
                  "to press reload, press reload again to engage the reload.")
            self.reload_enabled = True
            return
        tic = time.time()
        if not self.initialized:
            print("Reloading initial board state...")
            with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
                username = f.read()
            with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
                password = g.read()
            api_key = tygron.join_session(username, password)
            if api_key is None:
                print("logging in to Tygron failed, running Virtual River without "
                      "Tygron")
                self.tygron = False
            else:
                self.token = "token=" + api_key
                print("logged in to Tygron")
            # get image from camera
            img = webcam.get_image(self.turn, mirror=True)
            print("Trying to get an initial board image")
            # calibrate camera
            # try - except TypeError --> if nothing returned by method, then go to
            # test mode.
            try:
                canvas, thresh = cali.detect_corners(img, method='adaptive',
                                                     path=self.processing_path)
            except TypeError:
                self.test = True
                print("TEST MODE: No camera detected, loading stored "
                      "configuration file")
            # adjust image, get the hexagons and store calibration values as global
            # variables.
            if not self.test:
                self.pers, self.img_x, self.img_y, self.origins, self.radius, \
                    cut_points, self.hexagons = cali.rotate_grid(canvas, thresh)
                print("Calibrated camera.")
                # create the calibration file for use by other methods and store it
                # change dir_path to config_path
                self.transforms = cali.create_calibration_file(
                        self.img_x, self.img_y, cut_points, path=self.config_path)
            else:
                self.transforms = cali.create_calibration_file(
                    path=self.config_path, test = self.test)
            self.hexagons_sandbox = gridmap.read_hexagons(
                        filename='hexagons%d.geojson' % self.turn,
                        path=self.store_path)
            self.node_grid = gridmap.read_hexagons(
                        filename='node_grid%d.geojson' % self.turn,
                        path=self.store_path)
            self.filled_node_grid = gridmap.read_hexagons(
                        filename='filled_node_grid%d.geojson' % self.turn,
                        path=self.store_path)
            self.flow_grid = gridmap.read_hexagons(
                        filename='flow_grid%d.geojson' % self.turn,
                        path=self.store_path)
            if self.tygron:
                self.hexagons_sandbox = tygron.update_hexagons_tygron_id(
                        self.token, self.hexagons_sandbox)
                self.hexagons_tygron = detect.transform(
                        self.hexagons_sandbox, self.transforms,
                        export="sandbox2tygron")
            print("Reloaded and transformed geojson featurecollections.")
            # initialize Delft3D-FM model
            tac = time.time()
            #self.model = D3D.initialize_model()
            if self.tygron:
                # a geotiff of the node grid is required to set the elevation in
                # tygron.
                t0 = time.time()
                self.heightmap = gridmap.create_geotiff(
                    self.node_grid, turn=self.turn, path=self.store_path)
                print("Created geotiff elevation map")
                self.hexagons_tygron = tygron.set_terrain_type(
                        self.token, self.hexagons_tygron)
                tygron.hex_to_terrain(self.token, self.hexagons_tygron)
                file_location = (self.store_path + "\\grid_height_map" +
                                 str(self.turn) + ".tif")
                heightmap_id = tygron.set_elevation(
                        file_location, self.token, turn=self.turn)
                t1 = time.time()
                print("Updated Tygron world from current board state.")
            """
            # run the model. --> this is currently separate from the initialization
            # as the whole system becomes rather slow. Added a temporary run model
            # button to the Virtual River GUI to run the model instead.
            self.fig, self.axes = D3D.run_model(
                    self.model, self.filled_node_grid, self.flow_grid,
                    self.hexagons_sandbox, initialized=self.initialized)
            """
            """
            # Not sure it makes sense to store the structures ?
            with open(os.path.join(self.store_path,
                                   'structures.geojson'), 'w') as f:
                geojson.dump(weirs, f, sort_keys=True,
                             indent=2)
            print("Saved structures file (conditional).")
            """
            self.scores()
            # system is now initialized
            self.initialized = True
            toc = time.time()
            try:
                print("Finished startup and calibration" +
                      ". Calibration and loading time: " +
                      str(round(tac-tic, 2)) +
                      " seconds. Tygron terrain update time: " +
                      str(round(t1-t0, 2)) +
                      " seconds. Total initialization time: " +
                      str(round(toc-tic, 2)) + " seconds.")
            except UnboundLocalError:
                print("Finished startup and calibration" +
                      ". Calibration and loading time: " +
                      str(round(tac-tic, 2)) +
                      " seconds. Total initialization time: " +
                      str(round(toc-tic, 2)) + " seconds.")
            
            self.update_viz()
            return
        else:
            tic = time.time()
            #hexagons_sandbox_old = deepcopy(self.hexagons_sandbox)
            try:
                print("Getting board state of " + str(self.turn) +
                      " from storing folder.")
                self.hexagons_sandbox = gridmap.read_hexagons(
                        filename='hexagons%d.geojson' % self.turn,
                        path=self.store_path)
                self.node_grid = gridmap.read_hexagons(
                        filename='node_grid%d.geojson' % self.turn,
                        path=self.store_path)
                self.filled_node_grid = gridmap.read_hexagons(
                        filename='filled_node_grid%d.geojson' % self.turn,
                        path=self.store_path)
                self.flow_grid = gridmap.read_hexagons(
                        filename='flow_grid%d.geojson' % self.turn,
                        path=self.store_path)
                print("Reloaded board state of turn " + str(self.turn) + " .")
            except FileNotFoundError:
                print("ERROR: You have reloaded to the last stored file. "
                      "Please continue to play through update.")
                return
            # THIS SHOULD BE MOVED TO INITIALIZE AFTER MODEL IS FIXED TO INITIALIZATION
            if not self.ghost_hexagons_fixed:
                self.hexagons_sandbox = ghosts.update_values(
                        self.hexagons_sandbox)
                self.ghost_hexagons_fixed = True
                print("Fixed the ghost cell values")
            if self.tygron:
                # update hexagon ids to matching ids in tygron.
                self.hexagons_sandbox = tygron.update_hexagons_tygron_id(
                        self.token, self.hexagons_sandbox)
            self.hexagons_sandbox, self.turn_costs, dike_moved = compare.compare_hex(
                    self.cost_module, self.hexagons_prev,
                    self.hexagons_sandbox)
            #self.total_costs = self.total_costs + turn_costs
            # update the Chezy coefficients of all hexagons.
            tac = time.time()
            if self.tygron:
                # transform the hexagons to the sandbox coordinates --> check if this
                # is necessary, as the main hexagons are already updated, they should
                # be linked in memory to the sandbox hexagons.
                t0 = time.time()
                self.hexagons_tygron = detect.transform(
                        self.hexagons_sandbox, self.transforms,
                        export="sandbox2tygron")
                # get the hexagons that should be changed to water or land in
                # tygron.
                #hexagons_to_water, hexagons_to_land = compare.terrain_updates(
                #        self.hexagons_tygron)
                # update tygron terrain
                tygron.set_terrain_type(
                        self.token, self.hexagons_tygron)
                tygron.hex_to_terrain(self.token, self.hexagons_tygron)
                t1 = time.time()

            toc = time.time()
            if self.tygron:
                # create a new geotiff and set the new elevation in tygron.
                t2 = time.time()
                self.heightmap = gridmap.create_geotiff(
                        self.node_grid, turn=self.turn, path=self.store_path)
                file_location = (self.store_path + "\\grid_height_map" +
                                 str(self.turn) + ".tif")
                heightmap_id = tygron.set_elevation(
                        file_location, self.token, turn=0)
                print("Updated Tygron heightmap.")
                t3 = time.time()
            """
            # run the model. --> this is currently separate from the initialization
            # as the whole system becomes rather slow. Added a temporary run model
            # button to the Virtual River GUI to run the model instead.
            self.fig, self.axes = D3D.run_model(
                        self.model, self.filled_node_grid, self.flow_grid,
                        self.hexagons_sandbox, initialized=self.initialized,
                        fig=self.fig, axes=self.axes)
            """
            self.scores()
            self.start_new_turn = False
            print("Turn costs: " + str(self.turn_costs) + ". Total costs: " +
                  str(self.total_costs + self.turn_costs))
            try:
                print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Tygron update time: " +
                  str(round((t1-t0)+(t3-t2), 2)) +
                  " seconds. Total update time: " + str(round(t3-tic, 2)) +
                  " seconds.")
            except UnboundLocalError:
                print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Total update time: " +
                  str(round(toc-tic, 2)) + " seconds.")
            self.update_viz()
            return

    def end_round(self):
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run "
                  "initialize")
            return
        if self.start_new_turn:
            print("It appears as if you have pressed end_round twice, there"
                  "has been no update from the previous board state so far.")
            return
        print("Ending round " + str(self.turn) + ", applying all the changes. "
              "Make sure to save the files for this turn!")
        """
        TODO: code to handle whatever needs to be handled, e.g. the indicators.
        """
        self.update_costs()
        self.store_previous_turn()
        # if self.save is defined as True, the end of turn files are
        # automatically stored.
        if self.save:
            self.save_files()
        self.start_new_turn = True
        self.turn += 1
        return

    def save_files(self):
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run "
                  "initialize")
            return
        with open(os.path.join(self.store_path,
                               'hexagons%d.geojson' % self.turn), 'w') as f:
            geojson.dump(self.hexagons_sandbox, f, sort_keys=True, indent=2)
        # Could change this to a try/except UnboundLocalError
        print("Saved hexagon file for turn " + str(self.turn) + ".")
        with open(os.path.join(self.store_path,
                               'node_grid%d.geojson' % self.turn), 'w') as f:
            geojson.dump(self.node_grid, f, sort_keys=True, indent=2)
        print("Saved node grid for turn " + str(self.turn) + ".")
        with open(os.path.join(self.store_path,
                               'filled_node_grid%d.geojson' % self.turn),
                  'w') as f:
            geojson.dump(self.filled_node_grid, f, sort_keys=True, indent=2)
        print("Saved filled node grid for turn " + str(self.turn) + ".")
        with open(os.path.join(self.store_path,
                               'flow_grid%d.geojson' % self.turn), 'w') as f:
            geojson.dump(self.flow_grid, f, sort_keys=True, indent=2)
        print("Saved flow grid for turn " + str(self.turn) + ".")
        return

    def update_costs(self):
        self.total_costs = self.total_costs + self.turn_costs
        self.turn_costs = 0
        return

    def store_previous_turn(self):
        self.hexagons_prev = deepcopy(self.hexagons_sandbox)
        """
        TEST THIS WITH THE TABLE --> comparison when updating should always be
        with the board of the previous turn, rather than the previous update.
        """
        #self.node_grid_prev = deepcopy(self.node_grid)
        #self.filled_node_grid_prev = deepcopy(self.filled_node_grid)
        return
    
    def scores(self):
        if not self.initialized:
            print("Virtual River is not yet initialized, there are no scores "
                  "to show, please first run initialize")
            return
        costs = self.total_costs + self.turn_costs
        self.indicators.add_indicator_values(50.0, 50.0, costs, self.turn)
        self.indicators.update_water_and_dike_levels(
                self.hexagons_sandbox, self.hexagons_prev, self.turn)
        self.indicators.update_flood_safety_score(self.turn)
        self.indicators.update_biodiversity_score(self.hexagons_sandbox,
                                                  self.turn)
        self.indicators.plot(self.turn)
        return
    
    def update_viz(self):
        self.viz.loop()

def main():
    app = QApplication(sys.argv)
    gui = GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
