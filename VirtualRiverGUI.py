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
from copy import deepcopy
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QCoreApplication


class GUI(QWidget):
    def __init__(self):
        super(GUI, self).__init__()
        self.initUI()

    def initUI(self):
        """
        app = QApplication([])
        window = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Top'))
        layout.addWidget(QPushButton('Bottom'))
        window.setLayout(layout)
        window.show()
        app.exec_()
        """
        self.script = runScript()
        btn_update = QPushButton('Update', self)
        btn_update.clicked.connect(self.on_update_button_clicked)
        btn_update.resize(180, 40)
        btn_update.move(20, 35)
        btn_initialize = QPushButton('Initialize', self)
        btn_initialize.clicked.connect(self.on_initialize_button_clicked)
        btn_initialize.resize(180, 40)
        btn_initialize.move(20, 80)
        btn_exit = QPushButton('Exit', self)
        btn_exit.clicked.connect(self.on_exit_button_clicked)
        btn_exit.resize(180, 40)
        btn_exit.move(20, 170)
        self.setWindowTitle('Virtual River interface')
        self.show()  # app.exec_()

    def on_update_button_clicked(self):
        print("Calling update function")
        self.script.update()

    def on_initialize_button_clicked(self):
        print("Calling update function")
        self.script.initialize()

    def on_exit_button_clicked(self):
        alert = QMessageBox()
        alert.setText('Exiting Virtual River')
        alert.exec_()
        QCoreApplication.instance().quit()


class runScript():
    def __init__(self):
        super(runScript, self).__init__()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.store_path = os.path.join(path, 'storing_files')
        try:
            os.mkdir(self.store_path)
            print("Directory ", self.store_path, " Created.")
        except FileExistsError:
            print("Directory ", self.store_path,
                  " already exists, overwriting files.")
        self.model_path = os.path.join(self.dir_path, 'models',
                                       'Waal_schematic')
        self.initialized = False
        self.turn = 0
        self.save = False
        self.token = ""
        self.model = None
        self.hexagons = None
        self.hexagons_sandbox = None
        self.hexagons_tygron = None
        self.transforms = None
        self.node_grid = None
        self.filled_node_grid = None
        self.face_grid = None
        self.heightmap = None
        self.pers = None
        self.img_x = None
        self.img_y = None
        self.origins = None
        self.radius = None

    def initialize(self):
        tic = time.time()
        with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
            username = f.read()
        with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
            password = g.read()
        api_key = tygron.join_session(username, password)
        if api_key is None:
            print("logging in to Tygron failed, unable to make changes in Tygron")
        else:
            self.token = "token=" + api_key
            print("logged in to Tygron")
            img = webcam.get_image(self.turn, mirror=True)
            print("retrieved initial board image")
            # camera calibration --> to do: initiation
            # changed filename as variable to img
            canvas, thresh = cali.detect_corners(img, method='adaptive',
                                                 path=self.dir_path)
            # store calibration values as global variables
            self.pers, self.img_x, self.img_y, self.origins, self.radius, \
                cut_points, features = cali.rotate_grid(canvas, thresh)
            # create the calibration file for use by other methods and store it
            self.transforms = cali.create_calibration_file(
                    self.img_x, self.img_y, cut_points, path=self.dir_path)
            print("calibrated camera")
            self.hexagons = detect.detect_markers(
                    img, self.pers, self.img_x, self.img_y, self.origins,
                    self.radius, features, method='LAB',path=self.dir_path)
            print("processed initial board state")
            
            self.hexagons = tygron.update_hexagons_tygron_id(self.token,
                                                             self.hexagons)
            self.hexagons_sandbox = detect.transform(
                    self.hexagons, self.transforms, export="sandbox",
                    path=self.dir_path)
            self.hexagons_sandbox = structures.determine_dikes(
                    self.hexagons_sandbox)
            self.hexagons_sandbox = structures.determine_channel(
                    self.hexagons_sandbox)
            channel = structures.get_channel(self.hexagons_sandbox)
            weirs = structures.create_structures(channel)
            """
            structures_tygron = detect.transform(weirs,
                                                 self.transforms,
                                                 export="sandbox2tygron")
            """
            hexagons_tygron_int = detect.transform(self.hexagons,
                                                   self.transforms,
                                                   export="tygron_initialize")
            self.hexagons_tygron = detect.transform(self.hexagons,
                                                    self.transforms,
                                                    export="tygron")
            print("prepared geojson files")
            self.model = D3D.initialize_model()
            self.node_grid = gridmap.read_node_grid(path=self.dir_path)
            self.face_grid = gridmap.read_face_grid(self.model,
                                                    path=self.dir_path)
            print("loaded grid")
            self.node_grid = gridmap.index_node_grid(self.hexagons_sandbox,
                                                     self.node_grid)
            self.face_grid = gridmap.index_face_grid(self.hexagons_sandbox,
                                                     self.face_grid)
            self.node_grid = gridmap.interpolate_node_grid(
                    self.hexagons_sandbox, self.node_grid, turn=self.turn,
                    path=self.dir_path)
            self.hexagons_sandbox, self.face_grid = roughness.hex_to_points(
                    self.model, self.hexagons_sandbox, self.face_grid)
            print("executed grid interpolation")
            self.filled_node_grid = deepcopy(self.node_grid)
            filled_hexagons = deepcopy(self.hexagons_sandbox)
            filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
            self.filled_node_grid = gridmap.update_node_grid(
                    filled_hexagons, self.filled_node_grid, fill=True)
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    filled_hexagons, self.filled_node_grid, turn=self.turn,
                    path=self.dir_path)
            print("executed grid fill interpolation")
            self.heightmap = gridmap.create_geotiff(
                    self.node_grid, turn=self.turn, path=self.dir_path)
            print("created geotiff")
            """
            This section is not very efficient, once the system is up and
            running replace this to either also check which hexagons need to
            change or make an empty project area that is either land or water
            only.
            """
            self.hexagons_tygron = tygron.set_terrain_type(
                    self.token, self.hexagons_tygron)
            tygron.hex_to_terrain(self.token, self.hexagons)
            file_location = (self.dir_path + "\\grid_height_map" +
                             str(self.turn) + ".tif")
            heightmap_id = tygron.set_elevation(file_location, self.token,
                                                turn=self.turn)
            print("updated Tygron")
            print("stored initial board state")
            toc = time.time()
            print("Start up and calibration time: "+str(toc-tic))
            self.initialized = True
            if self.save:
                with open(os.path.join(self.store_path,
                                       'hexagons%d.geojson' % self.turn),
                          'w') as f:
                    geojson.dump(self.hexagons_sandbox, f, sort_keys=True,
                                 indent=2)
                print("saved hexagon file (conditional)")
                with open(os.path.join(self.dir_path,
                                       'hexagons_tygron_initialization%d.geojson'
                                       % self.turn), 'w') as f:
                    geojson.dump(hexagons_tygron_int, f, sort_keys=True,
                                 indent=2)
                print("saved hexagon file (conditional)")
                with open(os.path.join(self.store_path,
                                       'node_grid%d.geojson' % self.turn),
                          'w') as f:
                    geojson.dump(self.node_grid, f, sort_keys=True,
                                 indent=2)
                with open(os.path.join(self.store_path,
                                       'filled_node_grid%d.geojson' % turn),
                          'w') as f:
                    geojson.dump(self.filled_node_grid, f, sort_keys=True,
                                 indent=2)
                print("saved interpolation files (conditional)")
                with open(os.path.join(self.store_path,
                                       'structures.geojson'), 'w') as f:
                    geojson.dump(weirs, f, sort_keys=True,
                                 indent=2)
                print("saved structures file (conditional)")
        return

    def update(self):
        """
        function that initiates and handles all update steps. Returns all update
        variables
        """
        if not self.initialized:
            print("Virtual River is not yet calibrated, please first run initialize")
            return
        tic = time.time()
        print("Updating board state")
        img = webcam.get_image(self.turn, mirror=True)
        print("retrieved board image after turn " + str(self.turn))
        hexagons_old = deepcopy(self.hexagons)
        self.hexagons = detect.detect_markers(img, self.pers, self.img_x, self.img_y, self.origins,
                                             self.radius, self.hexagons, turn=self.turn,
                                             method='LAB', path=self.dir_path)
        print("processed current board state")
        # this next update should not be necessary if tygron IDs are
        # properly updated at an earlier stage
        self.hexagons = tygron.update_hexagons_tygron_id(self.token, self.hexagons)
        self.hexagons, dike_moved = compare.compare_hex(self.token, hexagons_old,
                                                       self.hexagons)
        if dike_moved:
            self.hexagons = structures.determine_dikes(self.hexagons)
        self.hexagons_sandbox = detect.transform(self.hexagons, self.transforms,
                                            export="sandbox")
        self.hexagons_sandbox, self.face_grid = roughness.hex_to_points(self.model,
                                                              self.hexagons_sandbox,
                                                              self.face_grid)
        
            print("saved hexagon file for turn " + str(self.turn) + " (conditional)")
        self.hexagons_tygron = detect.transform(self.hexagons, self.transforms,
                                           export="tygron")
        hexagons_to_water, hexagons_to_land = compare.terrain_updates(
                self.hexagons_tygron)
        tygron.set_terrain_type(self.token, hexagons_to_water, terrain_type="water")
        tygron.set_terrain_type(self.token, hexagons_to_land, terrain_type="land")
        tygron.hex_to_terrain(self.token, self.hexagons_tygron)
        tac = time.time()
        self.node_grid = gridmap.update_node_grid(self.hexagons_sandbox, self.node_grid,
                                             turn=self.turn)
        self.node_grid = gridmap.interpolate_node_grid(self.hexagons_sandbox, self.node_grid,
                                                  turn=self.turn, save=False,
                                                  path=self.dir_path)
        """
        face grid update call should be added here. In addition, all geojson
        changed parameters should be changed to z_changed and landuse_changed
        """
        if dike_moved:
            filled_hexagons = deepcopy(self.hexagons_sandbox)
            self.filled_node_grid = deepcopy(self.node_grid)
            filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
            self.filled_node_grid = gridmap.update_node_grid(
                    filled_hexagons, self.filled_node_grid, fill=True)
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    filled_hexagons, self.filled_node_grid, turn=self.turn, save=False,
                    path=self.dir_path)
            print("updated complete grid, dike relocation detected")
        else:
            self.filled_node_grid = gridmap.update_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid, turn=self.turn)
            self.filled_node_grid = gridmap.interpolate_node_grid(
                    self.hexagons_sandbox, self.filled_node_grid, turn=self.turn, save=False,
                    path=self.dir_path)
        self.heightmap = gridmap.create_geotiff(self.node_grid, turn=self.turn, path=self.dir_path)
        file_location = (self.dir_path + "\\grid_height_map" + str(self.turn) + ".tif")
        heightmap_id = tygron.set_elevation(file_location, self.token, turn=0)
        if self.save:
            with open(os.path.join(self.store_path, 'hexagons%d.geojson' % self.turn),
                      'w') as f:
                geojson.dump(self.hexagons_sandbox, f, sort_keys=True,
                             indent=2)
            with open(os.path.join(self.dir_path, 'node_grid%d.geojson' % self.turn),
                      'w') as f:
                geojson.dump(self.node_grid, f, sort_keys=True,
                             indent=2)
            with open(os.path.join(self.dir_path, 'filled_node_grid%d.geojson' % self.turn),
                      'w') as f:
                geojson.dump(self.filled_node_grid, f, sort_keys=True,
                             indent=2)
            print("saved grid files for turn " + str(self.turn) + " (conditional)")
        toc = time.time()
        print("Updated to turn " + str(self.turn) +
              ". Comparison update time: " + str(tac-tic) +
              ". Interpolation update time: " + str(toc-tac) +
              ". Total update time: " + str(toc-tic))
        return


def main():
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
