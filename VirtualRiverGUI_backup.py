# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:35:25 2019

@author: HaanRJ
"""

import sys
import time
import geojson
#import keyboard
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
        self.setWindowTitle('Test')
        self.show()  # app.exec_()

    def on_update_button_clicked(self):
        alert = QMessageBox()
        alert.setText('Updating Virtual River')
        alert.exec_()
        start = self.script.getStart()
        print(start)
        if start:
            self.script.updateStart()

    def on_initialize_button_clicked(self):
        alert = QMessageBox()
        alert.setText('Initializing Virtual River')
        alert.exec_()
        start = self.script.getTurn()
        print(start)
        self.script.updateTurn()

    def on_exit_button_clicked(self):
        alert = QMessageBox()
        alert.setText('Exiting Virtual River')
        alert.exec_()
        QCoreApplication.instance().quit()
        
        
class runScript():
    def __init__(self):
        super(runScript, self).__init__()
        self.start = True
        self.turn = 0
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
        

    def getStart(self):
        return self.start
        
    def getTurn(self):
        return self.turn
    
    def updateStart(self):
        self.start = False
        return
        
    def updateTurn(self):
        self.turn += 1
        return
    

def main():
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
