# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:56:30 2019

@author: straa005
"""
import os
#import time
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import biosafe as bsf
import generateBoards as boards
from geojson import load, dump
from copy import deepcopy


class BiosafeVR():
    def __init__(self):
        """
        Constructor.
        """
        self.bsf_model = None
        self.legal_weights = None
        self.links_law = None
        self.links_eco1 = None
        self.links_eco2 = None
        self.lut = None
        self.vr_eco = None
        self.PotTax_reference = None
        self.PotTax_intervention = None
        self.PotTax_increase = None
        self.PotTax_percentage = None
        self.PotTax_avg = None
        self.PotTax_percentage_avg = None
        self.PotTax_max = None
        self.PotTax_percentage_max = None
        self.save_error = True
        self.set_variables()
        self.setup_biosafe()
        return


    def pjoin(self, in_dir, file_name):
        """
        Function to join path and filename.
        """
        return os.path.join(in_dir, file_name)


    def set_variables(self):
        """
        Function that loads and sets the necessary variables.
        """
        root_dir = os.path.dirname(os.path.realpath(__file__))
        self.scratch_dir = os.path.join(root_dir, 'scratch')
        self.input_dir  = os.path.join(root_dir, 'input_data')
        os.chdir(self.scratch_dir)
        
        # Input data BIOSAFE
        self.legal_weights = pd.read_csv(
                self.pjoin(self.input_dir, 'legalWeights.csv'), index_col = 0)
        self.links_law = pd.read_csv(
                self.pjoin(self.input_dir, 'linksLaw.csv'), index_col = 0)
        self.links_eco1 = pd.read_csv(
                self.pjoin(self.input_dir, 'linksEco.csv'), index_col = 0)
        self.lut = pd.read_excel(
                self.pjoin(self.input_dir, 'BIOSAFE_20190711.xlsx'),
                sheet_name = 'lut_RWES').fillna(method='ffill')

            # this lookup table (lut) has:
            #       ecotope codes of BIOSAFE in the 1st column: oldEcotope
            #       aggregated/translated ectotopes in 2nd column: newEcotope

        # Ecotopes used in Virtual River
        self.vr_eco = pd.read_csv(
                self.pjoin(self.input_dir, 'VR_ecotopes.csv'))

        # Aggregate BIOSAFE ecotopes into RWES ecotopes
        self.links_eco2 = bsf.aggregateEcotopes(self.links_eco1, self.lut)
        return


    def setup_biosafe(self):
        """
        Sets up biosafe and stores it as an object variable.
        """
        # Generate dummy data in the right format
        species_presence = pd.DataFrame(
                np.random.randint(2, size=len(self.links_law)),
                columns=['speciesPresence'], index=self.links_law.index)

        ecotope_area = pd.DataFrame(
                np.ones(len(self.links_eco2.columns)-1) * 1e5,
                columns = ['area_m2'],
                index = self.links_eco2.columns.values[0:-1])

        # Simplify ecotope tables to VR ecotopes
        unique_eco = np.unique(
                np.hstack((self.vr_eco.ecotope1.values,
                           self.vr_eco.ecotope2.values)))
        links_eco3 = self.links_eco2.reindex(columns=unique_eco)
        ecotope_area = ecotope_area.reindex(index=unique_eco)

        # Run a first version of Biosafe
        self.bsf_model = bsf.biosafe(
                self.legal_weights, self.links_law, links_eco3,
                species_presence, ecotope_area)

        #PotTax = self.bsf_model.TFI()
        #PotAll = self.bsf_model.FI()
        return


    def ecotope_area_sums(self, board):
        """
        Calculate the total area of all ecotopes on the playing board.

        input:
            board: GeoDataFrame 
                   with columns geometry, z_reference, landuse and biosafe
            vr_ecotopes: Dataframe with two ecotope fractions per label
                   as defined in the Virtual River
            
        Returns a dataframe with the total area per ecotope in hexagons.
        """

        # clean up the input and merge into a single dataframe
        cols = ['geometry', 'z_reference', 'landuse', 'biosafe']
        board_clean = board.loc[board.biosafe, cols]
        board_eco = pd.merge(board_clean, self.vr_eco,
                             on=['z_reference', 'landuse'])

        # optional: output gdf to shp
        #    gdf = board_eco.copy()
        #    gdf['biosafe'] = gdf.biosafe.values.astype('int')
        #    gdf.to_file('board_eco.shp')

        # calculate the total area of all columns
        # note: landuse-z_reference combinations not in vr_ecotopes are
        # excluded
        area_eco1 = board_eco.groupby('ecotope1').sum()
        area_eco2 = board_eco.groupby('ecotope2').sum()
        area_fractions = pd.concat([area_eco1.fraction1, area_eco2.fraction2],
                                   axis=1, sort=True)
        area_total = area_fractions.fillna(0).sum(axis=1).reset_index()
        area_total.columns = ['ecotope', 'area_m2']    

        # assert that that total area of the ecotopes matches the biosafe
        # hexagons
        try:
            assert int(area_total.sum().area_m2) == int(board_clean.shape[0]),\
            ("ERROR: There appears to be one or more polygons that is not " +
            "detected correctly, resulting in a missmatch of the VR ecotopes")
        except AssertionError as error:
            print(error)
            if self.save_error:
                
                self.save_error = False
            pass

        area_out = area_total.set_index('ecotope')
        area_out.index.name=None
        return area_out


    def process_board(self, hexagons, reference=False):
        """
        Function that processes the current board (including the initial board
        at the start of the Virtual River game).
        """
        # Input data Virtual River
        board = gpd.GeoDataFrame.from_features(hexagons.features)
        if reference:
            self.board_reference = board
        else:
            self.board_intervention = board

        # Evaluate the board
        eco_area = self.ecotope_area_sums(board)
        self.bsf_model.ecotopeArea = eco_area
        PotTax = self.bsf_model.TFI()
        if reference:
            self.PotTax_reference = PotTax
        else:
            self.PotTax_intervention = PotTax
        return


    def plot(self):
        """
        Function to plot the biosafe output, not called as such in the Virtual
        River.
        """
        # plot the data for checking
        fig, [[ax1,ax2],[ax3,ax4], [ax5,ax6]] = plt.subplots(
                3,2, figsize=(10,8))

        # Relative height
        self.board_reference.plot(
                column='z_reference', cmap='GnBu_r', legend=True, ax=ax1)
        self.board_max.plot(
                column='z_reference', cmap='GnBu_r', legend=True, ax=ax2)

        # Landuse
        self.board_reference.plot(
                column='landuse', legend=True, ax=ax3, cmap='viridis',
                scheme='equal_interval', k=11)
        self.board_max.plot(
                column='landuse', legend=True, ax=ax4, cmap='viridis',
                scheme='equal_interval', k=11)

        index = np.arange(7)
        xticks = self.PotTax_reference.index.values
        bar_width = 0.3

        # plot the initial and new situation comparison
        label = ("reference: " +
                 str(round(self.PotTax_reference.sum().TFI, 2)))
        reference = ax5.bar(
                index, self.PotTax_reference.values.flatten(), bar_width,
                label=label, tick_label=xticks)
        label = ("avg intervention: " +
                 str(round(self.PotTax_avg.sum().TFI, 2)))
        avg = ax5.bar(
                index+bar_width, self.PotTax_avg.values.flatten(),
                bar_width, label=label, tick_label=xticks)
        label = ("max intervention: " +
                 str(round(self.PotTax_max.sum().TFI, 2)))
        maxi = ax5.bar(
                index+bar_width*2, self.PotTax_max.values.flatten(),
                bar_width, label=label, tick_label=xticks)
        ax5.set_ylabel("total value")
        ax5.legend(loc='best')
        for tick in ax5.get_xticklabels():
            tick.set_rotation(90)

        # plot the percentage increase/decrease between the initial and new
        # situation
        data = self.PotTax_percentage.values.flatten()
        percentage = ax6.bar(
                index, data, bar_width, label="percentage", tick_label=xticks)
        data2 = self.PotTax_percentage_avg.values.flatten()
        percentage_avg = ax6.bar(
                index+bar_width, data2, bar_width, label="avg percentage", tick_label=xticks)
        ax6.set_ylabel("increase (%)")
        data3 = self.PotTax_percentage_max.values.flatten()
        percentage_max = ax6.bar(
                index+bar_width, data3, bar_width, label="max percentage", tick_label=xticks)
        ax6.set_ylabel("increase (%)")
        minimum = min(data3)
        maximum = 0
        for value in data3:
            if value > maximum:
                maximum = value
        #maximum = max(data)
        size = len(str(int(round(maximum))))
        maximum = int(str(maximum)[:1])
        maximum = (maximum + 1) * (10**(size-1))
        ax6.set_ylim([min(0, minimum), maximum])
        for tick in ax6.get_xticklabels():
            tick.set_rotation(90)


    def compare(self):
        """
        Function that compares the intervention (current board state) with the
        reference (initial board state) and stores the differences between the
        two, both absolute and percentages.
        """
        self.PotTax_increase = self.PotTax_intervention - self.PotTax_reference
        self.PotTax_percentage = (
                (self.PotTax_increase / self.PotTax_reference) * 100)
        self.PotTax_increase = self.PotTax_avg - self.PotTax_reference
        self.PotTax_percentage_avg = (
                (self.PotTax_increase / self.PotTax_reference) * 100)
        """
        self.PotTax_percentage['TFI'] = pd.Series(
                ["{0:.2f}%".format(val * 100) for val in
                 self.PotTax_percentage['TFI']],
                index = self.PotTax_percentage.index)
        """
        return


    def get_reference(self):
        """
        Getter for the reference (initial board state) biosafe output.
        """
        return self.PotTax_reference


    def get_intervention(self):
        """
        Getter for the current intervention (board state) biosafe output.
        """
        return self.PotTax_intervention


    def get_percentage(self):
        """
        Getter for the percentage difference.
        """
        return self.PotTax_percentage
    
    
    def print_output(self):
        print("Reference score: " + str(self.PotTax_reference.sum().TFI))
        print("Intervention score: " + str(self.PotTax_intervention.sum().TFI))
        print("Highest score: " + str(self.PotTax_max.sum().TFI))
        return
    
    
    def store_max(self):
        if self.PotTax_max is None:
            self.compare()
            self.PotTax_max = self.PotTax_intervention
            self.PotTax_percentage_max = self.PotTax_percentage
            self.board_max = self.board_intervention
        else:
            if self.PotTax_max.sum().TFI < self.PotTax_intervention.sum().TFI:
                self.compare()
                self.PotTax_max = self.PotTax_intervention
                self.PotTax_percentage_max = self.PotTax_percentage
                self.board_max = self.board_intervention
        return
    
    
    def store_average(self, count):
        if self.PotTax_avg is None:
            self.PotTax_avg = self.PotTax_intervention
        else:
            self.PotTax_avg = (
                    ((self.PotTax_avg * (count - 1)) +
                     self.PotTax_intervention) / count)
        return
    
    
    def save_max_board(self):
        hexagons = self.board_max.__geo_interface__
        with open("largest_board_max_score_1_in_8_z_3.geojson", 'w') as f:
            dump(hexagons, f, sort_keys=True, indent=2)
        return


def test():
    """
    Function to test the code separately from the Virtual River.
    """
    root_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(root_path, 'test_files')
    with open(os.path.join(test_path, 'hexagons_wide_basin.geojson')) as f:
        hexagons_old = load(f)
    with open(os.path.join(test_path, 'hexagons_wide_basin.geojson')) as f:
        hexagons_new = load(f)        
    return hexagons_new, hexagons_old


def main():
    hexagons_new, hexagons_old = test()
    biosafe = BiosafeVR()
    hexagons_old = boards.all_agriculture(hexagons_old)
    biosafe.process_board(hexagons_old, reference=True)
    hexagons_new = boards.all_agriculture(hexagons_new)
    #hexagons_new = boards.update_single_hexagon(hexagons_new)
    biosafe.process_board(hexagons_new)
    #biosafe.store_average(i)
    #biosafe.store_max()
    #print("Now at trial #" + str(i))
    biosafe.compare()
    biosafe.plot()
    biosafe.print_output()
    biosafe.save_max_board()


if __name__ == "__main__":
    main()
