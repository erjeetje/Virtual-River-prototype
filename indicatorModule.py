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
        """
        Needs to be reconsidered --> only relevant if plots are kept.
        """
        #self.fig.canvas.manager.full_screen_toggle()
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
        self.ax2.set_xlabel("dike section")
        self.ax2.set_ylabel("chance of flooding occurrence")
        # graph with water levels vs dike height
        self.ax3.set_xlabel("river length (meters)")
        self.ax3.set_ylabel("height (meters)")
        # graph with overall costs made
        self.ax6.set_ylabel("million Euros")
        
        self.ax1.set_ylim([0, 100])
        self.ax2.set_ylim([0, 100])
        self.ax3.set_ylim([14, 18])
        self.ax6.set_ylim([0, 25000000])
        
        self.ax1.set_title("Overall score on indicators")
        self.ax2.set_title("Flood safety levels")
        self.ax3.set_title("Normative water levels vs dike crest height")
        self.ax6.set_title("Budget spent")
        
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
        """
        Function that declares the initial variables, called by the
        constructor.
        """
        self.indicators = ["flood safety", "biodiversity", "costs"]
        self.flood_safety = []
        self.biodiversity = []
        self.cost_score = []
        self.total_costs = []
        self.turn = []
        self.biosafe_percentage = None
        self.biosafe_reference = None
        self.biosafe_intervention = None
        return


    def add_flood_safety_score(self, score, turn=0):
        if turn < len(self.turn):
            self.flood_safety[turn] = score
        else:
            self.flood_safety.append(score)
        return
    
    
    def add_biosafe_score(self, score, turn=0):
        if turn < len(self.turn):
            self.biodiversity[turn] = score
        else:
            self.biodiversity.append(score)
        return
    
    
    def add_cost_score(self, score, turn=0):
        if turn < len(self.turn):
            self.cost_score[turn] = score
        else:
            self.cost_score.append(score)
        return
    
    
    def add_total_costs(self, costs, turn=0):
        if turn < len(self.turn):
            self.total_costs[turn] = costs
        else:
            self.total_costs.append(costs)
        return
    
    
    def add_indicator_values(self, flood_safety_score, biodiversity_score,
                             cost_score, total_cost, turn=0):
        """
        Function that updates all the main scores. May need to be reconsidered.
        """        
        if turn < len(self.turn):
            self.flood_safety[turn] = flood_safety_score
            self.biodiversity[turn] = biodiversity_score * 100
            self.cost_score[turn] = cost_score * 100
            self.total_costs[turn] = total_cost
        else:
            self.flood_safety.append(flood_safety_score)
            self.biodiversity.append(biodiversity_score * 100)
            self.total_costs.append(total_cost)
            self.cost_score.append(cost_score * 100)
            self.turn.append(turn)
        return
    
    def calculate_cost_score(self, costs):
        cost_score = ((25000000 - costs) / 25000000)
        return cost_score
    
    
    def update_flood_safety_score(self, turn):
        """
        Needs to be reconsidered
        """
        flood_safety_score = (sum(self.flood_safety_level) / 3750) * 100
        if turn < len(self.turn):
            self.flood_safety[turn] = flood_safety_score
        else:
            self.flood_safety.append(flood_safety_score)
        return
    
    def update_biodiversity_score(self, hexagons, turn):
        """
        Temporary function to show a biodiversity score, now obsolete.
        """
        floodplain_count = 0
        non_eco_count = 0
        for feature in hexagons.features:
            if feature.properties["ghost_hexagon"]:
                continue
            if (feature.properties["floodplain_north"] or
                feature.properties["floodplain_south"]):
                floodplain_count += 1
                if (feature.properties["landuse"] == 0 or
                    feature.properties["landuse"] == 1):
                    non_eco_count += 1
        eco_score = (((floodplain_count - non_eco_count) /
                      floodplain_count) * 100)
        if turn < len(self.turn):
            self.biodiversity[turn] = eco_score
        else:
            self.biodiversity.append(eco_score)
        return
    
    def store_biosafe_output(self, data, reference=False, percentage=False):
        """
        This function is ok
        """
        if percentage:
            self.biosafe_percentage = data
        elif reference:
            self.biosafe_reference = data
        else:
            self.biosafe_intervention = data
        return
        
    
    def indicator_feedback_values(self):
        self.water_levels = []
        self.ref_water_levels = []
        self.original_water_levels = []
        self.dike_levels = []
        self.river_length = []
        self.costs = 0
        self.flood_safety_level = []
        self.ref_flood_safety_level = []
        self.initial_flood_safety_level = []
        return
    
    def update_flood_safety(self, flood_safety_values, ref_flood_safety_values, turn=0):
        self.flood_safety_level = flood_safety_values
        self.ref_flood_safety_level = ref_flood_safety_values
        if turn == 0:
            self.initial_flood_safety_level = ref_flood_safety_values
        return
    
    def update_flood_safety2(self, flood_safety_values, turn):
        lowest_flood_safety = min(flood_safety_values)
        if turn < len(self.turn):
            self.flood_safety_level[turn] = lowest_flood_safety 
        else:
            self.flood_safety_level.append(flood_safety_values)
        return
    
    def update_water_and_dike_levels(self, hexagons, hexagons_old, turn):
        water_levels = water.water_levels_new2(hexagons)
        self.water_levels = water_levels
        try:
            ref_water_levels = water.water_levels_new2(hexagons_old)
        except AttributeError:
            ref_water_levels = water_levels
        self.ref_water_levels = ref_water_levels
        if turn == 0:
            self.original_water_levels = ref_water_levels
        dike_levels = water.dike_levels(hexagons)
        self.dike_levels = dike_levels
        if not self.river_length:
            river_length = water.get_river_length(water_levels)
            self.river_length = river_length
        flood_safety_values = water.flood_safety(dike_levels, water_levels)
        ref_flood_safety_values = water.flood_safety(dike_levels, ref_water_levels)
        self.update_flood_safety(flood_safety_values, ref_flood_safety_values, turn=turn)
        return

    def plot(self, turn):
        plt.ioff()
        reference = [self.flood_safety[0], self.biodiversity[0], self.cost_score[0]]
        intervention = [self.flood_safety[turn], self.biodiversity[turn], self.cost_score[turn]]
        x_labels = [("turn " + str(self.turn[value])) for value in self.turn]
        self.ax1.clear()
        bar_width = 0.3
        offset = bar_width / 2
        self.barlist_ref = self.ax1.bar(self.x_pos-offset, reference, width=bar_width,
                                    align='center')
        self.barlist_ref[0].set_color('DodgerBlue')
        self.barlist_ref[1].set_color('LimeGreen')
        self.barlist_ref[2].set_color('Salmon')
        self.barlist_int = self.ax1.bar(self.x_pos+offset, intervention, width=bar_width,
                                    align='center')
        self.barlist_int[0].set_color('b')
        self.barlist_int[1].set_color('g')
        self.barlist_int[2].set_color('r')
        self.ax1.plot([-0.3, 0.3], [60, 60], "k--", color='r', label="minimum")
        self.ax1.plot([-0.3, 0.3], [80, 80], "k--", color='y', label="good")
        self.ax1.plot([-0.3, 0.3], [100, 100], "k--", color='g', label="excellent")
        self.ax1.plot([0.7, 1.3], [80, 80], "k--", color='y')
        self.ax1.plot([0.7, 1.3], [100, 100], "k--", color='g')
        self.ax1.plot([1.7, 2.3], [20, 20], "k--", color='y')
        self.ax1.plot([1.7, 2.3], [40, 40], "k--", color='g')
        self.ax1.set_ylim([0, 110])
        self.ax1.set_xticks(self.x_pos)
        self.ax1.set_xticklabels(self.indicators)
        self.ax1.set_xlabel("indicators")
        self.ax1.set_ylabel("score (%)")
        self.ax1.set_title("Overall score on indicators")
        self.ax1.legend(loc='best', fontsize='x-large')
        if not self.plot2:
            self.plot21, = self.ax2.plot([1,2,3], self.initial_flood_safety_level, label="initial flood safety levels", color='y')
            self.plot22, = self.ax2.plot([1,2,3], self.ref_flood_safety_level, label="previous turn flood safety levels", color='g')
            self.plot2, = self.ax2.plot([1,2,3], self.flood_safety_level, label="current flood safety levels", color='b')
        else:
            self.plot22.set_ydata(self.ref_flood_safety_level)
            self.plot2.set_ydata(self.flood_safety_level)
            if turn == 0:
                self.plot21.set_ydata(self.initial_flood_safety_level)
            
        self.ax2.set_xticks([1,2,3])
        self.ax2.set_xticklabels(["left (5 rows)", "middle (5 rows)", "right (5 rows)"])
        self.ax2.legend(loc='lower right', fontsize='x-large')
        #label = "dike crest height"
        if not self.plot3:
            self.plot3, = self.ax3.plot(self.river_length, self.dike_levels, label="dike crest height", color='r')
            self.plot31, = self.ax3.plot(self.river_length, self.original_water_levels, label="initial water levels", color='y')
            self.plot32, = self.ax3.plot(self.river_length, self.ref_water_levels, label="previous round water levels", color='g')
            self.plot33, = self.ax3.plot(self.river_length, self.water_levels, label="current water levels", color='b')
        else:
            self.plot3.set_ydata(self.dike_levels)
            self.plot32.set_ydata(self.ref_water_levels)
            self.plot33.set_ydata(self.water_levels)
            if turn == 0:
                self.plot31.set_ydata(self.original_water_levels)

        self.ax3.set_ylim([min(min(self.dike_levels)-2, 14), max(max(self.dike_levels)+2, 18)])
        self.ax3.legend(loc='best', fontsize='x-large')
        
        self.ax4.clear()
        index = np.arange(7)
        xticks = self.biosafe_reference.index.values
        self.plot4 = self.ax4.bar(index, self.biosafe_reference.values.flatten(), bar_width, label="reference", tick_label=xticks)
        if self.biosafe_intervention is not None:
            self.plot41 = self.ax4.bar(index+bar_width, self.biosafe_intervention.values.flatten(), bar_width, label="intervention", tick_label=xticks)
        self.ax4.legend(loc='best', fontsize='x-large')
        for tick in self.ax4.get_xticklabels():
            tick.set_rotation(90)
            
        self.ax5.clear()
        if self.biosafe_percentage is not None:
            data = self.biosafe_percentage.values.flatten()
            self.plot5 = self.ax5.bar(index, data, bar_width, label="reference", tick_label=xticks)
            self.ax5.set_ylabel("increase (%)")
            minimum = min(data)
            maximum = max(data)
            maximum = int(str(maximum)[:1])
            maximum = (maximum + 1) * 10
            self.ax5.set_ylim([min(0, minimum), maximum])
            for tick in self.ax5.get_xticklabels():
                tick.set_rotation(90)
        
        self.ax6.clear()
        self.plot6 = self.ax6.plot(self.turn, self.total_costs, color='r')
        self.ax6.set_ylim([0, max(25000000, max(self.total_costs))])
        self.ax6.set_xticks(self.turn)
        self.ax6.set_xticklabels(x_labels)
        self.ax6.set_ylabel("million Euros")
        self.ax6.set_title("Budget spent")
        #self.fig.canvas.draw()
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

    turn += 1
    hexagons_new = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    #cost = Costs()
    #cost.cost_per_hex()
    indicators = Indicators()
    #indicators.set_score(0, 0, 0, 0, turn=5)
    indicators.add_indicator_values(50, 50, 100, 0)
    indicators.add_indicator_values(60, 30, 80, 1)
    indicators.add_indicator_values(70, 30, 60, 2)
    indicators.add_indicator_values(70, 60, 40, 3)
    indicators.update_flood_safety([600, 400, 800], [600, 400, 600])
    indicators.update_water_and_dike_levels(hexagons, hexagons_new, turn)
    indicators.plot(3)


if __name__ == '__main__':
    main()