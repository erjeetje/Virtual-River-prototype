# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 10:00:28 2022

@author: HaanRJ
"""

import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QMessageBox,
                             QLabel, QDialog, QDesktopWidget, QVBoxLayout,
                             QHBoxLayout, QMainWindow)
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QFont


class Indicator_screen(QWidget):
    def __init__(self, path):
        super(Indicator_screen, self).__init__()
        self.setWindowTitle('Indicator screen')
        self.setFixedSize(1720, 1000)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.path = path
        self.turn_tracker = 0
        self.score_flood_safety = 0
        self.score_biodiversity = 0
        self.score_budget = 100
        self.red_locations = 0
        self.yellow_locations = 0
        self.green_locations = 0
        self.bio_initial_total = 0
        self.bio_current_total = 0
        self.budget_tracker = 17500000
        self.initUI()
        self.show()  # app.exec_()
        return
    
    def initUI(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.header_top = QHBoxLayout()
        self.images_top = QHBoxLayout()
        self.info_top1 = QHBoxLayout()
        self.info_top2 = QHBoxLayout()
        self.info_top3 = QHBoxLayout()
        self.blank = QHBoxLayout()
        self.header_bottom = QHBoxLayout()
        self.images_bottom = QHBoxLayout()
        self.info_bottom1 = QHBoxLayout()
        self.info_bottom2 = QHBoxLayout()
        self.info_bottom3 = QHBoxLayout()
        
        """
        Top header row (flood safety & biodiversity)
        """
        title_font = QFont("Segoe UI", 20)
        self.flood_title = QLabel("Flood Safety")
        self.flood_title.setStyleSheet('color: white;}')
        self.flood_title.setAlignment(Qt.AlignCenter)
        self.flood_title.setFont(title_font)
        self.header_top.addWidget(self.flood_title)
        score = str(self.score_flood_safety) + " %"
        self.flood_score = QLabel(score)
        self.flood_score.setStyleSheet('color: white;}')
        self.flood_score.setAlignment(Qt.AlignCenter)
        self.flood_score.setFont(title_font)
        self.header_top.addWidget(self.flood_score)
        self.bio_title = QLabel("Biodiversity")
        self.bio_title.setStyleSheet('color: white;}')
        self.bio_title.setAlignment(Qt.AlignCenter)
        self.bio_title.setFont(title_font)
        self.header_top.addWidget(self.bio_title)
        score = str(self.score_biodiversity) + " %"
        self.bio_score = QLabel("0 %")
        self.bio_score.setStyleSheet('color: white;}')
        self.bio_score.setAlignment(Qt.AlignCenter)
        self.bio_score.setFont(title_font)
        self.header_top.addWidget(self.bio_score)
        
        """
        Top images row (flood safety & biodiversity)
        """
        os.chdir(self.path)
        image_width = 390
        flood_image1_source = QPixmap("flood_safety_score1.png")
        self.flood_image1 = flood_image1_source.scaledToWidth(image_width)
        self.flood_image1_label = QLabel()
        self.flood_image1_label.setPixmap(self.flood_image1)
        self.images_top.addWidget(self.flood_image1_label)
        flood_image2_source = QPixmap("flood_safety_score2.png")
        self.flood_image2 = flood_image2_source.scaledToWidth(image_width)
        self.flood_image2_label = QLabel()
        self.flood_image2_label.setPixmap(self.flood_image2)
        self.images_top.addWidget(self.flood_image2_label)
        bio_image1_source = QPixmap("biodiversity_score1.png")
        self.bio_image1 = bio_image1_source.scaledToWidth(image_width)
        self.bio_image1_label = QLabel()
        self.bio_image1_label.setPixmap(self.bio_image1)
        self.images_top.addWidget(self.bio_image1_label)        
        bio_image2_source = QPixmap("biodiversity_score2.png")
        self.bio_image2 = bio_image2_source.scaledToWidth(image_width)
        self.bio_image2_label = QLabel()
        self.bio_image2_label.setPixmap(self.bio_image2)
        self.images_top.addWidget(self.bio_image2_label)       
        
        """
        Top info row (flood safety & biodiversity)
        """
        self.btn_update = QPushButton('Update', self)
        self.btn_update.clicked.connect(self.on_update_button_clicked)
        self.info_bottom3.addWidget(self.btn_update)
        content_font = QFont("Segoe UI", 13)
        
        """
        Flood safety information
        """
        self.flood_score_exp1 = QLabel("Minimum score: 50%")
        self.flood_score_exp1.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.flood_score_exp1.setFont(content_font)
        self.info_top1.addWidget(self.flood_score_exp1)
        self.flood_score_exp2 = QLabel("Good score: 65%")
        self.flood_score_exp2.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.flood_score_exp2.setFont(content_font)
        self.info_top2.addWidget(self.flood_score_exp2)
        self.flood_score_exp3 = QLabel("Excellent score: 80%")
        self.flood_score_exp3.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.flood_score_exp3.setFont(content_font)
        self.info_top3.addWidget(self.flood_score_exp3)
        
        text = "# of red locations (0 score contribution): " + str(self.red_locations)
        self.dike_score_exp1 = QLabel(text)
        self.dike_score_exp1.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.dike_score_exp1.setFont(content_font)
        self.info_top1.addWidget(self.dike_score_exp1)
        text = "# of yellow locations (0.5 score contribution): " + str(self.yellow_locations)
        self.dike_score_exp2 = QLabel(text)
        self.dike_score_exp2.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.dike_score_exp2.setFont(content_font)
        self.info_top2.addWidget(self.dike_score_exp2)
        text = "# of green locations (1 score contribution): " + str(self.green_locations)
        self.dike_score_exp3 = QLabel(text)
        self.dike_score_exp3.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.dike_score_exp3.setFont(content_font)
        self.info_top3.addWidget(self.dike_score_exp3)
        
        """
        Biodiversity information
        """
        self.bio_score_exp1 = QLabel("Minimum score: 50%")
        self.bio_score_exp1.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.bio_score_exp1.setFont(content_font)
        self.info_top1.addWidget(self.bio_score_exp1)
        self.bio_score_exp2 = QLabel("Good score: 65%")
        self.bio_score_exp2.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.bio_score_exp2.setFont(content_font)
        self.info_top2.addWidget(self.bio_score_exp2)
        self.bio_score_exp3 = QLabel("Excellent score: 80%")
        self.bio_score_exp3.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.bio_score_exp3.setFont(content_font)
        self.info_top3.addWidget(self.bio_score_exp3)
        
        self.taxo_score_exp1 = QLabel("Potential biodiversity (sum of taxonomic groups):")
        self.taxo_score_exp1.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.taxo_score_exp1.setFont(content_font)
        self.info_top1.addWidget(self.taxo_score_exp1)
        text = "Initial board: " + str(self.bio_initial_total)
        self.taxo_score_exp2 = QLabel(text)
        self.taxo_score_exp2.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.taxo_score_exp2.setFont(content_font)
        self.info_top2.addWidget(self.taxo_score_exp2)
        text = "Current board: " + str(self.bio_current_total)
        self.taxo_score_exp3 = QLabel(text)
        self.taxo_score_exp3.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.taxo_score_exp3.setFont(content_font)
        self.info_top3.addWidget(self.taxo_score_exp3)
        
        """
        Budget information
        """
        self.budget_title = QLabel("Budget")
        self.budget_title.setStyleSheet('color: white;}')
        self.budget_title.setAlignment(Qt.AlignCenter)
        self.budget_title.setFont(title_font)
        self.header_bottom.addWidget(self.budget_title)
        score = str(self.score_budget) + " %"
        self.budget_score = QLabel(score)
        self.budget_score.setStyleSheet('color: white;}')
        self.budget_score.setAlignment(Qt.AlignCenter)
        self.budget_score.setFont(title_font)
        self.header_bottom.addWidget(self.budget_score)
        self.turn_title = QLabel("Turn")
        self.turn_title.setStyleSheet('color: white;}')
        self.turn_title.setAlignment(Qt.AlignCenter)
        self.turn_title.setFont(title_font)
        self.header_bottom.addWidget(self.turn_title)
        self.turn_score = QLabel(str(self.turn_tracker))
        self.turn_score.setStyleSheet('color: white;}')
        self.turn_score.setAlignment(Qt.AlignCenter)
        self.turn_score.setFont(title_font)
        self.header_bottom.addWidget(self.turn_score)
        
        budget_image1_source = QPixmap("budget_score1.png")
        self.budget_image1 = budget_image1_source.scaledToWidth(image_width)
        self.budget_image1_label = QLabel()
        self.budget_image1_label.setPixmap(self.budget_image1)
        self.images_bottom.addWidget(self.budget_image1_label)
        budget_image2_source = QPixmap("budget_score2.png")
        self.budget_image2 = budget_image2_source.scaledToWidth(image_width)
        self.budget_image2_label = QLabel()
        self.budget_image2_label.setPixmap(self.budget_image2)
        self.images_bottom.addWidget(self.budget_image2_label)
        
        self.info_bottom1.addWidget(QLabel())
        self.info_bottom2.addWidget(QLabel())
        
        
        text = "Initial budget: 17500000 Euros"
        self.initial_budget = QLabel(text)
        self.initial_budget.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.initial_budget.setFont(content_font)
        self.info_bottom1.addWidget(self.initial_budget)
        text = "Remaining budget: " + str(self.budget_tracker) + " Euros"
        self.remaining_budget = QLabel(text)
        self.remaining_budget.setStyleSheet('color: white;}')
        #self.flood_score_exp1.setAlignment(Qt.AlignCenter)
        self.remaining_budget.setFont(content_font)
        self.info_bottom2.addWidget(self.remaining_budget)
        
        """
        empty labels to fix alignment (yes, very ugly solution for testing,
        to fix later)
        """
        self.images_bottom.addWidget(QLabel())
        self.images_bottom.addWidget(QLabel())
        self.info_bottom1.addWidget(QLabel())
        self.info_bottom1.addWidget(QLabel())
        self.info_bottom2.addWidget(QLabel())
        self.info_bottom2.addWidget(QLabel())
        
        """
        Layouts
        """
        self.layout.addLayout(self.header_top, 7)
        self.layout.addLayout(self.images_top, 28)
        self.layout.addLayout(self.info_top1, 4)
        self.layout.addLayout(self.info_top2, 4)
        self.layout.addLayout(self.info_top3, 4)
        self.layout.addLayout(self.blank, 6)
        self.layout.addLayout(self.header_bottom, 7)
        self.layout.addLayout(self.images_bottom, 28)
        self.layout.addLayout(self.info_bottom1, 4)
        self.layout.addLayout(self.info_bottom2, 4)
        self.layout.addLayout(self.info_bottom3, 4)
        
        #self.widget.setLayout(self.layout)
        #self.setCentralWidget(self.widget)
        self.setLayout(self.layout)
        self.setStyleSheet('background-color: #383e42;')
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        #self.show()
        return
    
    def on_update_button_clicked(self):
        self.set_flood_scores(score=53, red=5, yellow=5, green=5)
        self.set_bio_scores(score=61, pottax=115, pottax_ini=98)
        self.set_budget_scores(score=80, budget=20000000)
        self.update_images(1)
        self.update_scores(1)
        return
    
    def update_images(self, turn):
        os.chdir(self.path)
        image_width = 390
        flood_image1_source = QPixmap("flood_safety_score1.png")
        self.flood_image1 = flood_image1_source.scaledToWidth(image_width)
        self.flood_image1_label.setPixmap(self.flood_image1)
        flood_image2_source = QPixmap("flood_safety_score2.png")
        self.flood_image2 = flood_image2_source.scaledToWidth(image_width)
        self.flood_image2_label.setPixmap(self.flood_image2)
        bio_image1_source = QPixmap("biodiversity_score1.png")
        self.bio_image1 = bio_image1_source.scaledToWidth(image_width)
        self.bio_image1_label.setPixmap(self.bio_image1)     
        bio_image2_source = QPixmap("biodiversity_score2.png")
        self.bio_image2 = bio_image2_source.scaledToWidth(image_width)
        self.bio_image2_label.setPixmap(self.bio_image2)
        budget_image1_source = QPixmap("budget_score1.png")
        self.budget_image1 = budget_image1_source.scaledToWidth(image_width)
        self.budget_image1_label.setPixmap(self.budget_image1)     
        budget_image2_source = QPixmap("budget_score2.png")
        self.budget_image2 = budget_image2_source.scaledToWidth(image_width)
        self.budget_image2_label.setPixmap(self.budget_image2)
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        return
        
    def update_scores(self, turn): 
        self.turn_score.setText(str(turn))
        text = str(self.score_flood_safety) + " %"
        self.flood_score.setText(text)
        text = str(self.score_biodiversity) + " %"
        self.bio_score.setText(text)
        text = str(self.score_budget) + " %"
        self.budget_score.setText(text)
        
        text = "# of red locations (0 score contribution): " + str(self.red_locations)
        self.dike_score_exp1.setText(text)
        text = "# of yellow locations (0.5 score contribution): " + str(self.yellow_locations)
        self.dike_score_exp2.setText(text)
        text = "# of green locations (1 score contribution): " + str(self.green_locations)
        self.dike_score_exp3.setText(text)
        text = "Initial board: " + str(self.bio_initial_total)
        self.taxo_score_exp2.setText(text)
        text = "Current board: " + str(self.bio_current_total)
        self.taxo_score_exp3.setText(text)
        text = "Remaining budget: " + str(self.budget_tracker) + " Euros"
        self.remaining_budget.setText(text)
        return
    
    def set_flood_scores(self, score=0, red=0, yellow=0, green=0):
        self.score_flood_safety = round(score*100)
        self.red_locations = red
        self.yellow_locations = yellow
        self.green_locations = green
        return
        
    def set_bio_scores(self, score=0, pottax_ini=0, pottax=0):
        self.score_biodiversity = round(score*100)
        self.bio_initial_total = pottax_ini
        self.bio_current_total = pottax
        return
        
    def set_budget_scores(self, score=100, costs=0):
        self.score_budget = round(score*100)
        self.budget_tracker = 17500000 - costs
        return
        
        



def main():
    app = QApplication(sys.argv)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    store_path = os.path.join(dir_path, 'storing_files')
    indicators = Indicator_screen(store_path)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()