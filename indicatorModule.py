# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 11:23:26 2019

@author: HaanRJ
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import gridMapping as gridmap
import waterModule as water

class Indicators():  
    def __init__(self):
        super(Indicators, self).__init__()
        self.fig = plt.figure()
        self.default_indicator_values()
        self.indicator_feedback_values()
        self.set_figure_variables()

    def set_figure_variables(self):
        self.fig.canvas.manager.full_screen_toggle()
        self.gs = self.fig.add_gridspec(2, 3)
        self.ax1 = self.fig.add_subplot(self.gs[0, 0])
        self.ax2 = self.fig.add_subplot(self.gs[0, 1])
        self.ax3 = self.fig.add_subplot(self.gs[0, 2])
        self.ax4 = self.fig.add_subplot(self.gs[1, 0])
        self.ax5 = self.fig.add_subplot(self.gs[1, 1])
        self.ax6 = self.fig.add_subplot(self.gs[1, 2])
        # histogram with indicator scoring
        self.ax1.set_xlabel("indicators")
        self.ax1.set_ylabel("score (%)")
        # graph with flood safety levels
        self.ax2.set_ylabel("chance of flooding")
        # graph with water levels vs dike height
        self.ax3.set_ylabel("meters")
        # graph with overall biodiversity values
        self.ax4.set_ylabel("biomass (kg/m2)")
        # graph with flood safety levels
        self.ax5.set_ylabel("biodiversity per taxonomic group")
        # graph with overall costs made
        self.ax6.set_ylabel("million Euros")
        
        self.ax1.set_ylim([0, 100])
        self.ax2.set_ylim([0, 100])
        self.ax3.set_ylim([0, 6])
        self.ax4.set_ylim([0, 100])
        self.ax5.set_ylim([0, 100])
        self.ax6.set_ylim([0, 25])
        
        self.ax1.set_title("Overall score on indicators")
        self.ax2.set_title("Flood safety levels")
        self.ax3.set_title("Normative water levels vs dike crest height")
        self.ax4.set_title("Total biodiversity")
        self.ax5.set_title("Biodiversity per taxonomic group")
        self.ax6.set_title("")
        
        self.x_pos = np.arange(len(self.indicators))
        self.ax1.set_xticks(self.x_pos)
        self.ax1.set_xticklabels(self.indicators)
        
        flood_safety_levels = [100, 200, 400, 600, 800, 1000, 1250]
        self.ax2.set_yticks(flood_safety_levels)
        self.ax2.set_yticklabels(["1/"+str(value) for value in flood_safety_levels])
        
        self.plot1 = None
        self.plot2 = None
        self.plot3 = None
        self.plot4 = None
        self.plot5 = None
        self.plot6 = None
        return
    
    def default_indicator_values(self):
        self.indicators = ["flood safety", "biodiversity", "costs"]
        self.flood_safety = []
        self.biodiversity = []
        self.total_costs = []
        self.turn = []
        return
        
    def add_indicator_values(self, flood_safety_score, biodiversity_score,
                             cost_score, turn):
        if turn < len(self.turn):
            self.flood_safety[turn] = flood_safety_score
            self.biodiversity[turn] = biodiversity_score
            self.total_costs[turn] = cost_score
        else:
            self.flood_safety.append(flood_safety_score)
            self.biodiversity.append(biodiversity_score)
            self.total_costs.append(cost_score)
            self.turn.append(turn)
        return
    
    def indicator_feedback_values(self):
        self.water_levels = []
        self.dike_levels = []
        self.river_length = []
        self.costs = 0
        self.flood_safety_level = []
        return
    
    def update_flood_safety(self, flood_safety_values):
        self.flood_safety_level = flood_safety_values
        return
    
    def update_flood_safety2(self, flood_safety_values, turn):
        lowest_flood_safety = min(flood_safety_values)
        if turn < len(self.turn):
            self.flood_safety_level[turn] = lowest_flood_safety 
        else:
            self.flood_safety_level.append(flood_safety_values)
        return
    
    def update_water_and_dike_levels(self, hexagons):
        water_levels = water.water_levels(hexagons)
        self.water_levels = water_levels
        dike_levels = water.dike_levels(hexagons)
        self.dike_levels = dike_levels
        if not self.river_length:
            river_length = water.get_river_length(water_levels)
            self.river_length = river_length
        return

    def plot(self, turn):
        performance = [self.flood_safety[turn], self.biodiversity[turn],
                       self.total_costs[turn]]
        x_labels = [("turn " + str(self.turn[value])) for value in self.turn]
        self.ax1.clear()
        self.barlist = self.ax1.bar(self.x_pos, performance, align='center',
                                    width=0.2)
        self.barlist[0].set_color('b')
        self.barlist[1].set_color('g')
        self.barlist[2].set_color('r')
        if not self.plot2:
            self.plot2, = self.ax2.plot([1,2,3], self.flood_safety_level, color='b')
        else:
            self.plot2.set_ydata(self.flood_safety_level)
        self.ax2.set_xticks([1,2,3])
        self.ax2.set_xticklabels(["left (5 rows)", "middle (5 rows)", "right (5 rows)"])
        label = "dike crest height"
        if not self.plot3:
            self.plot3, = self.ax3.plot(self.river_length, self.dike_levels, label=label, color='r')
            #add a reference water level, either initial turn or start of new turn.
            #self.plot31, = self.ax3.plot(self.river_length, self.ref_water_levels, label=label, color='r')
            self.plot32, = self.ax3.plot(self.river_length, self.water_levels, label=label, color='b')
        else:
            self.plot3.set_ydata(self.dike_levels)
            self.plot32.set_ydata(self.water_levels)
        label = "normative water level"
        
        self.ax3.legend(loc='lower right', fontsize='x-large')
        #self.ax3.set_xticks(self.turn)
        #self.ax3.set_xticklabels(x_labels)
        self.ax4.clear()
        self.plot4 = self.ax4.plot(self.turn, self.biodiversity, color='g')
        self.ax4.set_xticks(self.turn)
        self.ax4.set_xticklabels(x_labels)
        #self.ax5.clear()
        #self.plot5 = self.ax5.plot(self.turn, self.total_costs, color='r')
        self.ax5.set_xticks(self.turn)
        self.ax5.set_xticklabels(x_labels)
        self.ax6.clear()
        self.plot6 = self.ax6.plot(self.turn, self.total_costs, color='r')
        self.ax6.set_xticks(self.turn)
        self.ax6.set_xticklabels(x_labels)
        self.fig.canvas.draw()
        return

    def set_score(self, scores, waterlevels, bio_value, total_costs, turn=0):
        turns = list(range(0, turn + 1))
        print(turns)
        return


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    turn = 0
    hexagons = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    """
    turn += 1
    hexagons_new = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    """
    #cost = Costs()
    #cost.cost_per_hex()
    indicators = Indicators()
    #indicators.set_score(0, 0, 0, 0, turn=5)
    indicators.add_indicator_values(50, 50, 100, 0)
    indicators.add_indicator_values(60, 30, 80, 1)
    indicators.add_indicator_values(70, 30, 60, 2)
    indicators.add_indicator_values(70, 60, 40, 3)
    indicators.update_flood_safety([600, 400, 800])
    indicators.update_water_and_dike_levels(hexagons)
    indicators.plot(3)


if __name__ == '__main__':
    main()