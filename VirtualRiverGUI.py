# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:35:25 2019

@author: HaanRJ
"""

import sys
import time
import geojson
import os
import pywinauto
import tygronInterface as tygron
import gridCalibration as cali
import processImage as detect
import gridMapping as gridmap
import updateFunctions as compare
import webcamControl as webcam
import modelInterface as D3D
import createStructures as structures
import costModule as costs
import waterModule as water
import ghostCells as ghosts
import hexagonAdjustments as adjust
import hexagonOwnership as owner
import visualization as visualize
import biosafeVR as biosafe
import localServer as server
from copy import deepcopy
from shutil import copyfile
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QMessageBox,
                             QLabel)
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QPainter, QPen


class GUI(QWidget):
    def __init__(self):
        super(GUI, self).__init__()
        self.script = runScript()
        self.setWindowTitle('Virtual River interface')
        self.setFixedSize(200, 1040)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.initUI()
        self.show()  # app.exec_()

    def initUI(self):
        lbl_update = QLabel('Update controls', self)
        lbl_update.move(10, 40)
        lbl_update.setFixedWidth(180)
        lbl_update.setAlignment(Qt.AlignCenter)
        btn_update = QPushButton('Update', self)
        btn_update.clicked.connect(self.on_update_button_clicked)
        btn_update.resize(180, 40)
        btn_update.move(10, 80)
        btn_round = QPushButton('End round', self)
        btn_round.clicked.connect(self.on_end_round_button_clicked)
        btn_round.resize(180, 40)
        btn_round.move(10, 160)
        lbl_viz = QLabel('Visualization controls', self)
        lbl_viz.move(10, 340)
        lbl_viz.setFixedWidth(180)
        lbl_viz.setAlignment(Qt.AlignCenter)
        btn_elevation = QPushButton('Elevation', self)
        btn_elevation.clicked.connect(self.on_elevation_button_clicked)
        btn_elevation.resize(180, 40)
        btn_elevation.move(10, 380)
        btn_flow = QPushButton('Flow velocities', self)
        btn_flow.clicked.connect(self.on_flow_button_clicked)
        btn_flow.resize(180, 40)
        btn_flow.move(10, 460)
        btn_roughness = QPushButton('Roughness', self)
        btn_roughness.clicked.connect(self.on_roughness_button_clicked)
        btn_roughness.resize(180, 40)
        btn_roughness.move(10, 540)
        btn_ownership = QPushButton('Ownership', self)
        btn_ownership.clicked.connect(self.on_ownership_button_clicked)
        btn_ownership.resize(180, 40)
        btn_ownership.move(10, 620)
        lbl_facilitator = QLabel('Facilitator controls', self)
        lbl_facilitator.move(10, 810)
        lbl_facilitator.setFixedWidth(180)
        lbl_facilitator.setAlignment(Qt.AlignCenter)
        btn_initialize = QPushButton('Initialize', self)
        btn_initialize.clicked.connect(self.on_initialize_button_clicked)
        btn_initialize.resize(180, 40)
        btn_initialize.move(10, 850)
        btn_reload = QPushButton('Reload', self)
        btn_reload.clicked.connect(self.on_reload_button_clicked)
        btn_reload.resize(180, 40)
        btn_reload.move(10, 930)
        return
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        painter.drawRect(5,10,190,230)
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        painter.drawRect(5,310,190,390)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        painter.drawRect(5,780,190,230)
        return
        

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
        
    def on_elevation_button_clicked(self):
        self.script.switch_viz(screen="elevation")
        
    def on_flow_button_clicked(self):
        self.script.switch_viz(screen="flow")
    
    def on_roughness_button_clicked(self):
        self.script.switch_viz(screen="roughness")

    def on_ownership_button_clicked(self):
        self.script.switch_viz(screen="ownership")


class runScript():
    """
    
    """
    def __init__(self):
        super(runScript, self).__init__()
        self.set_paths()
        self.set_variables()
        return


    def set_paths(self):
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
        self.web_path = os.path.join(self.dir_path, 'webserver')
        try:
            os.mkdir(self.web_path)
            print("Directory ", self.web_path, " Created.")
        except FileExistsError:
            print("Directory ", self.web_path,
                  " already exists, overwriting files.")
        self.model_path = os.path.join(self.dir_path, 'models',
                                       'Waal_schematic')
        self.config_path = os.path.join(self.dir_path, 'config_files')
        self.test_path = os.path.join(self.dir_path, 'test_files')
        return
    
    
    def set_variables(self):
        # the following variables are used to determine what functions the
        # script calls and which it skips. The variables are automatically
        # update in the initialization depending on whether or not a camera
        # is detected and a tygron session is found.
        self.initialized = False
        self.reload_enabled = False
        self.start_new_turn = False
        self.test = False
        self.tygron = True
        self.update_count = 0
        # save variables, adjust as you wish how to run Virtual River
        self.save = True
        self.model_save = False
        self.reloading = False
        self.debug = False
        # Virtual River variables. THESE ARE ADJUSTABLE!
        self.slope = 10**-3  # tested and proposed range: 10**-3 to 10**-4
        self.vert_scale = 1  # setting matches current z scaling, testing.
        # Mixtype vegetation class ratio in % for natural grass/reed/brushwood
        # Currently not used, but can be passed to landuse_to_friction function
        # of the updateRoughness module.
        self.mixtype_ratio = [50, 20, 30]
        # Memory variables
        self.turn = 0
        self.token = ""
        self.model = D3D.Model()
        self.turn_img = None
        #self.hexagons = None
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
        self.pers = None
        # may not be necessary to store these, but some methods would need to
        # be updated (in gridCalibration and processImage).
        self.img_x = None
        self.img_y = None
        self.origins = None
        self.radius = None
        # list that tracks groyne/LTDs updates during a turn (both have to be
        # reset if changes are reverted).
        self.groyne_tracker = []
        # water safety module
        self.water_module = water.Water()
        self.flood_safety_score = None
        # cost module
        self.cost_module = costs.Costs()
        # total costs made up until the end of the rounds ended
        self.total_costs = 0
        # turn costs of the current round
        self.turn_costs = 0
        self.cost_score = None
        # BIOSAFE module
        self.biosafe = biosafe.BiosafeVR()
        self.biosafe_score = None
        # visualization
        self.viz = visualize.Visualization(self.model)
        app = pywinauto.application.Application().connect(title_re='main')
        self.window = app.window(title_re='main')
        return


    def initialize(self):
        """
        Function that handles configuring and calibrating the game board.
        """
        if self.initialized:
            print("Virtual River is already initialized, please use Update "
                  "instead.")
            return
        tic = time.time()
        self.tygron_login()
        self.get_image()
        """
        An AttributeError was triggered at canvas[1] in the pilot session -->
        most likely a corner was not found (len(canvas) 3 instead of 4) -->
        When that happens, this should stop any update and retry.
        """
        continue_code = self.calibrate_camera()
        if not continue_code:
            print("failed to calibrate camera and not testing, aborting rest "
                  "of method")
            return
        self.transform_hexagons()
        found_hexagons = self.get_hexagons()
        if not found_hexagons:
            print("failed to get hexagons, aborting rest of method")
            return
        if self.tygron:
            self.tygron_update_buildings()
        self.create_grids()
        self.set_up_hexagons()
        self.process_hexagons()
        if self.tygron:
            self.tygron_transform()
        self.update_ownership_viz()
        tac = time.time()
        self.index_grids()
        self.set_up_structures()
        self.process_grids() 
        tec = time.time()
        if self.tygron:
            t0 = time.time()
            self.tygron_update()
            t1 = time.time()
        self.run_biosafe()
        self.update_cost_score()
        self.initialized = True
        self.index_model()
        self.run_model()
        self.update_water_module()
        self.scores()
        if self.tygron:
            self.tygron_set_indicators()
        self.save_files()
        # always reset the reloading variables in case reloading is used.
        self.reloading = False
        self.reload_enabled = False
        toc = time.time()
        try:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Tygron terrain update time: " +
                  str(round(t1-t0, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return
    
    
    def initialize_old(self):
        """
        Function that handles configuring and calibrating the game board.
        """
        if self.initialized:
            print("Virtual River is already initialized, please use Update "
                  "instead.")
            return
        tic = time.time()
        self.tygron_login()
        self.get_image()
        """
        An AttributeError was triggered at canvas[1] in the pilot session -->
        most likely a corner was not found (len(canvas) 3 instead of 4) -->
        When that happens, this should stop any update and retry.
        """
        self.calibrate_camera()
        self.transform_hexagons()
        self.get_hexagons()
        if self.tygron:
            self.tygron_update_buildings()
        self.create_grids()
        self.set_up_hexagons()
        self.process_hexagons()
        if self.tygron:
            self.tygron_transform()
        self.update_ownership_viz()
        tac = time.time()
        self.index_grids()
        self.set_up_structures()
        self.process_grids() 
        tec = time.time()
        if self.tygron:
            t0 = time.time()
            self.tygron_update()
            t1 = time.time()
        self.run_biosafe()
        self.update_cost_score()
        self.initialized = True
        self.index_model()
        self.run_model()
        self.update_water_module()
        self.scores()
        if self.tygron:
            self.tygron_set_indicators()
        self.save_files()
        toc = time.time()
        try:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Tygron terrain update time: " +
                  str(round(t1-t0, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Finished startup and calibration" +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return


    def update(self):
        """
        Function that handles updating the game board.
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
        self.start_new_turn = False
        self.update_count += 1
        self.prepare_turn()
        if not self.test:
            self.get_image()
            """
            An AttributeError was triggered at canvas[1] in the pilot session -->
            most likely a corner was not found (len(canvas) 3 instead of 4) -->
            When that happens, this should stop any update and retry.
            """
            continue_code = self.calibrate_camera()
            if not continue_code:
                print("failed to calibrate camera and not testing, aborting rest "
                      "of method")
                return
        #self.transform_hexagons()
        found_hexagons = self.get_hexagons()
        if not found_hexagons:
            print("failed to get hexagons, aborting rest of method")
            return
        if self.tygron:
            self.tygron_update_buildings()
            self.tygron_transform()
        dike_moved = self.compare_hexagons()
        self.process_hexagons(dike_moved=dike_moved)
        tac = time.time()
        self.update_ownership_viz()
        self.process_grids(dike_moved=dike_moved)
        tec = time.time()
        if self.tygron:
            t0 = time.time()
            self.tygron_update()
            t1 = time.time()
        self.run_biosafe()
        self.update_cost_score()
        self.run_model()
        self.update_water_module(dike_moved=dike_moved)
        self.scores()
        if self.tygron:
            self.tygron_set_indicators()
        self.save_files(end_round=False)
        # always reset the reloading variables in case reloading is used.
        self.reloading = False
        self.reload_enabled = False
        toc = time.time()
        try:
            print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Interpolation update time: " +
                  str(round(tec-tac, 2)) + " seconds. Tygron update time: " +
                  str(round((t1-t0), 2)) + " seconds. Model update time: " +
                  str(round(toc-tec, 2)) + " seconds. Total update time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Interpolation update time: " +
                  str(round(tec-tac, 2)) + " seconds. Model update time: " +
                  str(round(toc-tec, 2)) + " seconds. Total update time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return
    
    
    def update_old(self):
        """
        Function that handles updating the game board.
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
        self.start_new_turn = False
        self.update_count += 1
        self.prepare_turn()
        if not self.test:
            self.get_image()
            """
            An AttributeError was triggered at canvas[1] in the pilot session -->
            most likely a corner was not found (len(canvas) 3 instead of 4) -->
            When that happens, this should stop any update and retry.
            """
            self.calibrate_camera()
        #self.transform_hexagons()
        self.get_hexagons()
        if self.tygron:
            self.tygron_update_buildings()
            self.tygron_transform()
        dike_moved = self.compare_hexagons()
        self.process_hexagons(dike_moved=dike_moved)
        tac = time.time()
        self.update_ownership_viz()
        self.process_grids(dike_moved=dike_moved)
        tec = time.time()
        if self.tygron:
            t0 = time.time()
            self.tygron_update()
            t1 = time.time()
        self.run_biosafe()
        self.update_cost_score()
        self.run_model()
        self.update_water_module(dike_moved=dike_moved)
        self.scores()
        if self.tygron:
            self.tygron_set_indicators()
        self.save_files(end_round=False)
        toc = time.time()
        try:
            print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Interpolation update time: " +
                  str(round(tec-tac, 2)) + " seconds. Tygron update time: " +
                  str(round((t1-t0), 2)) + " seconds. Model update time: " +
                  str(round(toc-tec, 2)) + " seconds. Total update time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Updated to turn " + str(self.turn) +
                  ". Comparison update time: " + str(round(tac-tic, 2)) +
                  " seconds. Interpolation update time: " +
                  str(round(tec-tac, 2)) + " seconds. Model update time: " +
                  str(round(toc-tec, 2)) + " seconds. Total update time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return
    
    
    def reload(self):
        if not self.reload_enabled:
            print("Are you sure you want to iniate a reload? If you intended "
                  "to press reload, press reload again to engage the reload.")
            self.reload_enabled = True
            return
        self.reloading = True
        if not self.initialized:
            self.initialize()
        else:
            self.update()
        return
        
    
    def reload_old(self):
        if not self.reload_enabled:
            print("Are you sure you want to iniate a reload? If you intended "
                  "to press reload, press reload again to engage the reload.")
            self.reload_enabled = True
            return
        self.reloading = True
        tic = time.time()
        self.start_new_turn = False
        if not self.initialized:
            self.tygron_login()
            self.get_image()
            """
            An AttributeError was triggered at canvas[1] in the pilot session -->
            most likely a corner was not found (len(canvas) 3 instead of 4) -->
            When that happens, this should stop any update and retry.
            """
            self.calibrate_camera()
        self.get_hexagons()
        #self.transform_hexagons()
        #self.process_hexagons()
        if self.tygron:
            self.tygron_update_buildings()
            self.tygron_transform()
        dike_moved = False
        if self.initialized:
            dike_moved = self.compare_hexagons()
        self.update_ownership_viz()
        tac = time.time()
        if not self.initialized:
            self.create_grids()
            self.index_grids()
            self.set_up_structures()
        if dike_moved is None:
            self.process_grids()
        else:
            self.process_grids(dike_moved=dike_moved)
        tec = time.time()
        if self.tygron:
            t0 = time.time()
            self.tygron_update()
            t1 = time.time()
        self.run_biosafe()
        self.update_cost_score()
        if not self.initialized:
            self.initialized = True
        self.reload_enabled = False
        self.reloading = False
        self.run_model()
        self.update_water_module(dike_moved=dike_moved)
        self.scores()
        if self.tygron:
            self.tygron_set_indicators()
        toc = time.time()
        try:
            print("Finished reloading to turn " + str(self.turn) +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Tygron terrain update time: " +
                  str(round(t1-t0, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        except UnboundLocalError:
            print("Finished reloading to turn " + str(self.turn) +
                  ". Calibration and loading time: " + str(round(tac-tic, 2)) +
                  " seconds. Indexing and interpolation time: " +
                  str(round(tec-tac, 2)) +
                  " seconds. Model run time: " + str(round(toc-tec, 2)) +
                  " seconds. Total initialization time: " +
                  str(round(toc-tic, 2)) + " seconds.")
        self.update_viz()
        return


    def create_server(self):
        """
        Create a localhost webserver (not called, run an apache server instead)
        """
        server.run_server(self.web_path, path=self.dir_path)
        return
    
    
    def prepare_turn(self):
        """
        Reset the turn costs in the cost module to 0.
        """
        self.cost_module.reset_costs(turn=self.turn)
        return
    
    
    def get_image(self):
        """
        Get a camera image.
        """
        self.turn_img = webcam.get_image(self.turn, mirror=True)
        print("Retrieved initial board image")
        return


    def calibrate_camera(self):
        """
        Calibrate the camera/board.
        
        try - except TypeError --> if nothing returned by method, then go to
        # test mode.
        """
        t0 = time.time()
        try:
            canvas, thresh = cali.detect_corners(
                    self.turn_img, method='adaptive',
                    path=self.processing_path)
        except TypeError:
            self.test = True
            print("TEST MODE: No camera detected, entering test mode")
        if not self.test:
            #self.pers, self.img_x, self.img_y, self.origins, self.radius, \
            #    cut_points, self.hexagons = cali.rotate_grid(canvas, thresh)
            try:
                self.pers, self.img_x, self.img_y, cut_points = \
                        cali.rotate_grid(canvas, thresh)
            except AttributeError:
                if not self.initialized:
                    print("did not find all four calibration corners, "
                          "aborting initialization. Fix the problem (check "
                          "webcam picture) and try again.")
                else:
                    print("did not find all four calibration corners, "
                          "aborting update. Fix the problem (check "
                          "webcam picture) and try again.")
                return False
            print("Calibrated camera.")
            # create the calibration file for use by other methods and store it
            save_calibration = False
            if not self.initialized:
                self.hexagons_sandbox, self.origins, self.radius = cali.create_features(
                        self.img_y, self.img_x)
                save_calibration = True
            self.transforms = cali.create_calibration_file(
                    self.img_x, self.img_y, cut_points, path=self.config_path,
                    save=save_calibration)
        else:
            self.transforms = cali.create_calibration_file(
                    path=self.config_path, test=self.test)
        t1 = time.time()
        print("Camera calibration time: " + str(t1-t0))
        return True


    def transform_hexagons(self):
        """
        Function that transforms the hexagons to the coordinates that the
        SandBox / Tygron uses.
        """
        if not (self.test or self.reloading):
            # update the hexagons to initial board state.
            self.hexagons_sandbox = detect.transform(
                    self.hexagons_sandbox, self.transforms, export="sandbox",
                    path=self.dir_path)
        print("Transformed hexagons suitable for model and tygron.")
        return
    
    
    def get_hexagons(self):
        """
        Function that creates/gets the new hexagons. Gets them from either the
        camera (live mode) or file (test mode).
        """
        if not (self.test or self.reloading):
            self.hexagons_sandbox = detect.detect_markers(
                    self.turn_img, self.pers, self.img_x, self.img_y,
                    self.origins, self.radius, self.hexagons_sandbox, method='LAB',
                    path=self.store_path, debug=self.debug)
            if not self.initialized:
                self.hexagons_sandbox = ghosts.set_values(self.hexagons_sandbox)
        else:
            if self.reloading:
                path = self.store_path
                print("Reloading: Getting new board state from store folder.")
            else:
                path = self.test_path
                print("TEST MODE: Getting new board state from test folder.")
            try:
                self.hexagons_sandbox = gridmap.read_hexagons(
                        filename='hexagons%d.geojson' % self.turn,
                        path=path)
            except FileNotFoundError:
                if self.reloading:
                    print("No more files to reload")
                else:
                    print("No more files to test")
                return False
            """
            if self.test:
                self.hexagons_sandbox = adjust.test_mode_z_correction(
                        self.hexagons_sandbox)
                if not self.initialized:
                    self.hexagons_sandbox = ghosts.set_values(
                            self.hexagons_sandbox)
            """
        print("Retrieved board state.")
        return True


    def set_up_hexagons(self):        
        """
        Function that determines the location of the main channel, dikes and
        floodplains. Function also finds the neighbours of hexagons and
        generates ownership for the players (only called on initialization).
        """
        if self.reloading:
            return
        self.hexagons_sandbox = structures.determine_dikes(
                self.hexagons_sandbox)
        self.hexagons_sandbox = structures.determine_channel(
                self.hexagons_sandbox)
        self.hexagons_sandbox = \
                structures.determine_floodplains_and_behind_dikes(
                        self.hexagons_sandbox)
        self.hexagons_sandbox = owner.determine_neighbours(
                self.hexagons_sandbox)
        self.hexagons_sandbox = owner.generate_ownership(
                self.hexagons_sandbox)
        self.hexagons_sandbox = owner.determine_ownership(
                self.hexagons_sandbox)
        self.hexagons_sandbox = adjust.find_factory(
                self.hexagons_sandbox)
        return
    
    
    def process_hexagons(self, dike_moved=False):
        """
        Process the hexagons, add various properties.
        """
        if not self.reloading:
            if not self.initialized:
                self.hexagons_sandbox = adjust.add_bedslope(
                        self.hexagons_sandbox, self.slope)
                self.hexagons_sandbox = gridmap.hexagons_to_fill(
                        self.hexagons_sandbox)
            # not sure the z_correction is needed anymore.
            self.hexagons_sandbox = adjust.z_correction(
                        self.hexagons_sandbox, initialized=self.initialized)
        if dike_moved:
            self.hexagons_sandbox = structures.determine_dikes(
                        self.hexagons_sandbox)
            self.hexagons_sandbox = \
                structures.determine_floodplains_and_behind_dikes(
                        self.hexagons_sandbox)
            self.hexagons_sandbox = compare.update_behind_dikes(
                    self.hexagons_prev, self.hexagons_sandbox)
            self.hexagons_sandbox = gridmap.hexagons_to_fill(
                    self.hexagons_sandbox)
        return


    def compare_hexagons(self):
        """
        Compare the previous turn hexagons with the updated hexagons.
        """
        self.hexagons_sandbox, self.turn_costs, dike_moved = \
        compare.compare_hex(
                self.cost_module, self.hexagons_prev, self.hexagons_sandbox,
                turn=self.turn)
        self.cost_module.update_total_costs(self.turn_costs, turn=self.turn)
        return dike_moved


    def create_grids(self):
        """
        Function that generates the grids (only called on initialization).
        """
        self.node_grid = gridmap.read_node_grid(self.model.model,
                                                path=self.store_path)
        self.flow_grid = gridmap.create_flow_grid(self.model.model,
                                                  path=self.store_path)
        self.face_grid = gridmap.read_face_grid(self.model.model,
                                                path=self.store_path)
        return


    def index_grids(self):
        """
        Function that indexes the grids (only called on initialization).
        """
        self.node_grid = gridmap.index_node_grid(self.hexagons_sandbox,
                                                 self.node_grid, self.slope)
        self.flow_grid = gridmap.index_flow_grid(self.hexagons_sandbox,
                                                 self.flow_grid)
        self.hexagons_sandbox = gridmap.index_hexagons(self.hexagons_sandbox,
                                                       self.face_grid)
        self.face_grid = gridmap.grid_columns(self.face_grid)
        self.face_grid = self.water_module.determine_grid_river_axis(
                self.hexagons_sandbox, self.face_grid)
        return


    def set_up_structures(self):
        """
        Function that adds structures to the grids (only called on
        initialization).
        """
        channel = structures.get_channel(self.hexagons_sandbox)
        groynes = structures.create_groynes(channel)
        ltds = structures.create_LTDs(channel)
        self.node_grid = structures.index_structures(groynes, self.node_grid)
        self.node_grid = structures.index_structures(
                ltds, self.node_grid, mode="ltd")
        #self.node_grid = gridmap.add_bedslope(self.node_grid, slope=self.slope)
        self.node_grid = gridmap.set_active(self.node_grid)
        self.node_grid = structures.create_buildings(self.hexagons_sandbox,
                                                     self.node_grid)
        return


    def process_grids(self, dike_moved=False):
        """
        Function that handles the interpolation of the node grids, as well as
        roughness setting of the flow grid.
        """
        if self.initialized:
            self.node_grid, ignore = gridmap.update_node_grid(
                    self.hexagons_sandbox, self.node_grid,
                    were_groynes = self.groyne_tracker, turn=self.turn,
                    printing=True)
        self.node_grid = gridmap.interpolate_node_grid(
                self.hexagons_sandbox, self.node_grid, turn=self.turn,
                fill=False, path=self.dir_path)
        # set the Chezy coefficient for each hexagon (based on water levels
        # and trachytopes) 
        """
        self.hexagons_sandbox = self.model.update_waterlevel(
                self.hexagons_sandbox)
        self.hexagons_sandbox = roughness.landuse_to_friction(
                self.hexagons_sandbox, vert_scale=self.vert_scale,
                initialization=True)
        self.hexagons_sandbox, self.flow_grid = roughness.hex_to_points(
                self.model.model, self.hexagons_sandbox, self.flow_grid)
        """
        print("Executed grid interpolation.")
        # create a deepcopy of the node grid and fill the grid behind the
        # dikes. The filled node grid is for the hydrodynamic model.
        if not self.initialized:
            self.filled_node_grid = deepcopy(self.node_grid)
            self.filled_node_grid, self.groyne_tracker = \
            gridmap.update_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid, fill=True)
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid,
                    turn=self.turn, fill=True, path=self.dir_path)
        else:
            if dike_moved:
                # if the dike locations changed, make a deepcopy of the
                # node_grid and update it accordingly.
                self.filled_node_grid = deepcopy(self.node_grid)
                self.filled_node_grid, self.groyne_tracker = \
                gridmap.update_node_grid(
                        self.hexagons_sandbox, self.filled_node_grid,
                        were_groynes = self.groyne_tracker, fill=True)
            else:
                # if the dike locations did not change, a simple update
                # suffices.
                self.filled_node_grid, self.groyne_tracker = \
                gridmap.update_node_grid(
                        self.hexagons_sandbox, self.filled_node_grid,
                        were_groynes = self.groyne_tracker, turn=self.turn,
                        grid_type="filled")
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid,
                    turn=self.turn, fill=True, path=self.dir_path)
        return


    def tygron_login(self):
        """
        Function that handles logging in to Tygron (only called on
        initialization).
        """
        try:
            with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
                username = f.read()
            with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
                password = g.read()
            api_key = tygron.join_session(username, password)
        except FileNotFoundError:
            api_key = None
        if api_key is None:
            print("logging in to Tygron failed, running Virtual River without "
                  "Tygron")
            self.tygron = False
        else:
            self.token = "token=" + api_key
            print("logged in to Tygron")
        return


    def tygron_transform(self):
        """
        Transform the hexagon features to the internal coordinates used by
        Tygron.
        """
        self.hexagons_tygron = detect.transform(
                self.hexagons_sandbox, self.transforms,
                export="sandbox2tygron")
        return


    def tygron_update_buildings(self):
        """
        Function that handles updating the tygron IDs of the hexagons.
        """
        self.hexagons_sandbox = tygron.update_hexagons_tygron_id(
                self.token, self.hexagons_sandbox)
        return


    def tygron_update(self):
        """
        Function that handles updating the Tygron virtual world. Changes the
        localhost directory to the webserver to avoid problems with loading.
        """
        os.chdir(self.web_path)
        gridmap.create_geotiff(
            self.node_grid, turn=self.turn, path=self.store_path)
        print("Created geotiff elevation map")
        tygron.set_terrain_type(self.token, self.hexagons_tygron)
        tygron.hex_to_terrain(self.token, self.hexagons_tygron)
        file_location = (self.store_path + "\\grid_height_map" +
                         str(self.turn) + ".tif")
        heightmap_id = tygron.set_elevation(
                file_location, self.token, turn=self.turn)
        return
    
    
    def tygron_set_indicators(self):
        """
        Function that handles updating the indicators in Tygron. changes the
        localhost directory to the webserver to avoid problems with loading.
        """
        os.chdir(self.web_path)
        counts = self.water_module.get_dike_safety()
        tygron.set_indicator(self.flood_safety_score, self.token,
                             indicator="flood", index=self.turn, value=counts)
        PotTax = self.biosafe.get_PotTax_sum()
        tygron.set_indicator(self.biosafe_score, self.token,
                             indicator="biodiversity", index=self.turn,
                             value=PotTax)
        costs = self.total_costs + self.turn_costs
        tygron.set_indicator(self.cost_score, self.token,
                             indicator="budget", index=self.turn, value=costs)
        return


    def tygron_initialize(self):
        """
        This function is no longer necessary, but may be called in case a new
        Tygron project is created (currently not called).
        """
        hexagons_tygron_int = detect.transform(
                self.hexagons, self.transforms,
                export="tygron_initialize")
        return


    def update_ownership_viz(self, end_of_round=False):
        """
        Function that adds non-model visualizations to the visualization
        object.
        """
        ownership_viz = owner.visualize_ownership(
                self.hexagons_sandbox, end_of_round=end_of_round)
        self.viz.add_image("OWNERSHIP", ownership_viz)
        return


    def index_model(self):
        """
        Function that indexes the model to only the visualized area (only
        called on initialization, not sure this is still necessary).
        """
        self.model.set_indexes(self.filled_node_grid, self.face_grid)
        return


    def run_model(self):
        """
        Function that handles running the model.
        """
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run initialize")
            return
        if self.turn == 0:
            print("Running model after initialization, updating the elevation "
                  "in the model will take some time. Running a maximum of 50 "
                  "loops to stabilize.")
        else:
            print("Running model after turn update, running a maximum of 10 "
                  "loops to stabilize.")
        self.hexagons_sandbox, self.flow_grid = self.model.run_model(
            self.filled_node_grid, self.hexagons_sandbox, self.flow_grid,
            turn=self.turn)
        if self.model_save:
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
            print("stored hexagon files with model output (conditional)")
        return


    def update_water_module(self, dike_moved=False):
        """
        This function handles all things related to the water module/flood
        safety indicator.
        """
        if (self.turn == 0 or dike_moved):
            self.water_module.determine_dike_levels(self.hexagons_sandbox)
            self.water_module.get_dike_location(self.hexagons_sandbox)
            self.water_module.index_dikes(self.face_grid)
        if self.turn == 0:
            self.water_module.determine_x_hexagons()
        self.face_grid = self.water_module.grid_river_axis_water_levels(
                self.face_grid, self.model.model, turn=self.turn)
        if self.turn == 0:
            self.water_module.determine_x_grid()
        self.water_module.determine_dike_water_level(turn=self.turn)
        self.water_module.determine_flood_safety_score()
        self.flood_safety_score = self.water_module.get_flood_safety_score()
        self.water_module.water_level_graph()
        self.water_module.dike_safety_graph()
        return
    
    
    def run_biosafe(self):
        """
        This function handles all things related to BIOSAFE/biodiversity
        indicator.
        """
        self.hexagons_sandbox = adjust.biosafe_area(self.hexagons_sandbox)
        if not self.initialized:
            self.biosafe.process_board(self.hexagons_sandbox, reference=True)
        else:
            self.biosafe.process_board(self.hexagons_sandbox, reference=False)
            self.biosafe.compare()
        self.biosafe.set_score()
        self.biosafe_score = self.biosafe.get_score()
        self.biosafe.biodiversity_graph(graph="score")
        self.biosafe.biodiversity_graph(graph="percentage")
        return


    def end_round(self):
        """
        This function ends a game round, saves the board and resets variables.
        """
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run "
                  "initialize")
            return
        if self.start_new_turn:
            print("It appears as if you have pressed end_round twice, there "
                  "has been no update from the previous board state so far.")
            return
        print("Ending round " + str(self.turn) + ", applying all the changes. "
              "Make sure to save the files for this turn!")
        """
        TODO: code to handle whatever needs to be handled, e.g. the indicators.
        """
        self.store_costs()
        self.store_previous_turn()
        # if self.save is defined as True, the end of turn files are
        # automatically stored.
        if self.save:
            self.save_files()
        if self.tygron:
            tygron.set_turn_tracker(self.turn, self.token)
        self.hexagons_sandbox = owner.reset_change(self.hexagons_sandbox)
        self.update_ownership_viz(end_of_round=True)
        self.copy_images()
        self.update_count = 0
        self.groyne_tracker = []
        self.start_new_turn = True
        self.turn += 1
        return
    
    
    def copy_images(self):
        filenames_src = ["flood_safety_score1.png", "flood_safety_score2.png",
                         "biodiversity_score1.png", "biodiversity_score2.png",
                         "budget_score1.png", "budget_score2.png"]
        filenames_dst = ["flood_safety_score1_turn%d.png" % self.turn,
                         "flood_safety_score2_turn%d.png" % self.turn,
                         "biodiversity_score1_turn%d.png" % self.turn,
                         "biodiversity_score2_turn%d.png" % self.turn,
                         "budget_score1_turn%d.png" % self.turn,
                         "budget_score2_turn%d.png" % self.turn]
        for src_name, dst_name in zip(filenames_src, filenames_dst):
            src = os.path.join(self.web_path, src_name)
            dst = os.path.join(self.store_path, dst_name)
            copyfile(src, dst)
        return


    def save_files(self, end_round=True):
        """
        This function save the game board, both intermediate and end of round.
        """
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run "
                  "initialize")
            return
        if not self.test:
            if end_round:
                filename = 'hexagons%d.geojson' % self.turn
            else:
                filename = ('hexagons%d' % self.turn + '_' +
                            str(self.update_count) + '.geojson')
            with open(os.path.join(self.store_path, filename), 'w') as f:
                geojson.dump(
                        self.hexagons_sandbox, f, sort_keys=True, indent=2)
            print("Saved hexagon file for turn " + str(self.turn) + ".")
        if self.debug:
            with open(os.path.join(
                    self.store_path,
                    'hexagons_debug%d.geojson' % self.turn), 'w') as f:
                geojson.dump(
                        self.hexagons_sandbox, f, sort_keys=True, indent=2)
            print("Saved hexagon file for turn " + str(self.turn) + ".")
            with open(os.path.join(
                    self.store_path,
                    'node_grid%d.geojson' % self.turn), 'w') as f:
                geojson.dump(self.node_grid, f, sort_keys=True, indent=2)
            print("Saved node grid for turn " + str(self.turn) + ".")
            with open(os.path.join(
                    self.store_path,
                    'filled_node_grid%d.geojson' % self.turn),
                      'w') as f:
                geojson.dump(
                        self.filled_node_grid, f, sort_keys=True, indent=2)
            print("Saved filled node grid for turn " + str(self.turn) +
                  ".")
            with open(os.path.join(
                    self.store_path,
                    'flow_grid%d.geojson' % self.turn), 'w') as f:
                geojson.dump(self.flow_grid, f, sort_keys=True, indent=2)
            print("Saved flow grid for turn " + str(self.turn) + ".")
            with open(os.path.join(
                    self.store_path,
                    'face_grid%d.geojson' % self.turn), 'w') as f:
                geojson.dump(self.face_grid, f, sort_keys=True, indent=2)
            print("Saved face grid for turn " + str(self.turn) + ".")
        return


    def store_costs(self):
        self.total_costs = self.total_costs + self.turn_costs
        self.turn_costs = 0
        return
    
    
    def update_cost_score(self):
        costs = self.total_costs + self.turn_costs
        self.cost_score = self.cost_module.calculate_cost_score(costs)
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
        self.cost_module.costs_graph()
        self.cost_module.costs_graph_breakdown()
        self.hexagons_sandbox = self.model.update_waterlevel(self.hexagons_sandbox)
        if not self.initialized:
            print("Virtual River is not yet initialized, there are no scores "
                  "to show, please first run initialize")
            return
        #self.indicators.add_flood_safety_score(50, self.turn)
        #self.indicators.add_biosafe_score(self.biosafe_score, self.turn)
        #self.indicators.add_cost_score(self.cost_score, self.turn)
        #costs = self.total_costs + self.turn_costs
        #self.indicators.add_total_costs(costs, self.turn)
        #self.indicators.add_indicator_values(
        #        50.0, self.biosafe_score, self.cost_score, costs,
        #        turn=self.turn)
        #self.indicators.update_water_and_dike_levels(
        #        self.hexagons_sandbox, self.hexagons_prev, self.turn)
        #self.indicators.update_flood_safety_score(self.turn)
        #if self.turn == 0:
        #    biosafe_ref = self.biosafe.get_reference()
        #    self.indicators.store_biosafe_output(biosafe_ref, reference=True)
        #biosafe_int = self.biosafe.get_intervention()
        #self.indicators.store_biosafe_output(biosafe_int)
        #biosafe_perc = self.biosafe.get_percentage()
        #self.indicators.store_biosafe_output(biosafe_perc, percentage=True)
        #self.indicators.plot(self.turn)
        return


    def print_costs(self):
        print("Turn costs: " + str(self.turn_costs) + ". Total costs: " +
              str(self.total_costs + self.turn_costs))
        return
    
    
    def switch_viz(self, screen="elevation"):
        if screen == "flow":
            key = '6'
        elif screen == "roughness":
            key = '8'
        elif screen == "ownership":
            key = '9'
        else:
            key = '5'
        self.window.set_focus()
        self.window.type_keys(key)
        


    def update_viz(self):
        self.viz.loop()


def main():
    app = QApplication(sys.argv)
    gui = GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
