# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:56:30 2019

@author: straa005
"""
import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import biosafe as bsf
from geojson import load


class BiosafeVR():
    def __init__(self):
        self.bsf_model = None
        self.legal_weights = None
        self.links_law = None
        self.links_eco1 = None
        self.links_eco2 = None
        self.lut = None
        self.vr_eco = None
        tic = time.time()
        self.set_variables()
        tec = time.time()
        self.setup_biosafe()
        tac = time.time()
        hexagons_new, hexagons_old = self.test()
        self.compare(hexagons_new, hexagons_old)
        toc = time.time()
        print("Load time: " + str(tec-tic))
        print("Setup time: " + str(tac-tec))
        print("Process time: " + str(toc-tac))
        return
        
    def pjoin(self, in_dir, file_name):
        return os.path.join(in_dir, file_name)
    
    def set_variables(self):
        root_dir = os.path.dirname(os.path.realpath(__file__))
        #root_dir = os.path.dirname(os.getcwd())
        self.scratch_dir = os.path.join(root_dir, 'scratch')
        self.input_dir  = os.path.join(root_dir, 'input_data')
        os.chdir(self.scratch_dir)
        
        # Input data BIOSAFE
        self.legal_weights = pd.read_csv(self.pjoin(self.input_dir, 'legalWeights.csv'), index_col = 0)
        self.links_law = pd.read_csv(self.pjoin(self.input_dir, 'linksLaw.csv'), index_col = 0)
        self.links_eco1 = pd.read_csv(self.pjoin(self.input_dir, 'linksEco.csv'), index_col = 0)
        self.lut = pd.read_excel(self.pjoin(self.input_dir, 'BIOSAFE_20190711.xlsx'),
                             sheet_name = 'lut_RWES').fillna(method='ffill')
            # this lookup table (lut) has:
            #       ecotope codes of BIOSAFE in the first column: oldEcotope
            #       aggregated/translated ectotopes in the second column: newEcotope
        
        # Ecotopes used in Virtual River
        self.vr_eco = pd.read_csv(self.pjoin(self.input_dir, 'VR_ecotopes.csv'))
        
        # Aggregate BIOSAFE ecotopes into RWES ecotopes
        self.links_eco2 = bsf.aggregateEcotopes(self.links_eco1, self.lut)
        return
    
    
    def setup_biosafe(self):
        # Generate dummy data in the right format
        species_presence = pd.DataFrame(np.random.randint(2, size=len(self.links_law)),
                                        columns=['speciesPresence'],
                                        index=self.links_law.index)
        
        ecotope_area = pd.DataFrame(np.ones(len(self.links_eco2.columns)-1) * 1e5,
                                    columns = ['area_m2'],
                                    index = self.links_eco2.columns.values[0:-1])
        
        # Simplify ecotope tables to VR ecotopes
        unique_eco = np.unique(np.hstack((self.vr_eco.ecotope1.values, self.vr_eco.ecotope2.values)))
        links_eco3 = self.links_eco2.reindex(columns=unique_eco)
        ecotope_area = ecotope_area.reindex(index=unique_eco)
        
        # Run a first version of Biosafe
        self.bsf_model = bsf.biosafe(self.legal_weights, self.links_law, links_eco3,
                      species_presence, ecotope_area)
        
        PotTax = self.bsf_model.TFI()
        PotAll = self.bsf_model.FI()
        return
    
    
    def test(self):
        root_path = os.path.dirname(os.path.realpath(__file__))
        test_path = os.path.join(root_path, 'test_files')
        with open(os.path.join(test_path, 'hexagons0.geojson')) as f:
            hexagons_old = load(f)
        with open(os.path.join(test_path, 'hexagons7.geojson')) as f:
            hexagons_new = load(f)        
        return hexagons_new, hexagons_old
    
    
    def ecotope_area_sums(self, board):
        """Calculate the total area of all ecotopes on the playing board.
        
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
        # note: landuse-z_reference combinations not in vr_ecotopes are excluded
        area_eco1 = board_eco.groupby('ecotope1').sum()
        area_eco2 = board_eco.groupby('ecotope2').sum()
        area_fractions = pd.concat([area_eco1.fraction1, area_eco2.fraction2],
                                   axis=1, sort=True)
        area_total = area_fractions.fillna(0).sum(axis=1).reset_index()
        area_total.columns = ['ecotope', 'area_m2']    
        
        # assert that that total area of the ecotopes matches the biosafe hexagons
        assert int(area_total.sum().area_m2) == int(board_clean.shape[0])
        
        area_out = area_total.set_index('ecotope')
        area_out.index.name=None
        return area_out
    
    
    def compare(self, hexagons_new, hexagons_old, plot=False):
        # Input data Virtual River
        board_reference = gpd.GeoDataFrame.from_features(hexagons_old.features)
        board_intervention = gpd.GeoDataFrame.from_features(hexagons_new.features)
        
        # Evaluate initial board
        eco_area_reference = self.ecotope_area_sums(board_reference)
        self.bsf_model.ecotopeArea = eco_area_reference
        PotTax_reference = self.bsf_model.TFI()
        #PotAll_reference = self.bsf_model.FI()
        #bsf.output2xlsx(bsf_model, 'bsf_reference.xlsx')
        
        # Evaluate new board
        eco_area_intervention = self.ecotope_area_sums(board_intervention)
        self.bsf_model.ecotopeArea = eco_area_intervention
        PotTax_intervention = self.bsf_model.TFI()
        #PotAll_intervention = self.bsf_model.FI()
        #bsf.output2xlsx(bsf_model, 'bsf_intervention.xlsx')
        
        # plot the data for checking
        if plot:
            fig, [[ax1,ax2],[ax3,ax4], [ax5,ax6]] = plt.subplots(3,2, figsize=(10,8))
            
            # Relative height
            board_reference.plot(column='z_reference', cmap='GnBu_r', legend=True, ax=ax1)
            board_intervention.plot(column='z_reference', cmap='GnBu_r', legend=True, ax=ax2)
            
            # Landuse
            board_reference.plot(column='landuse', legend=True, ax=ax3,
                                 cmap='viridis', scheme='equal_interval', k=11)
            board_intervention.plot(column='landuse', legend=True, ax=ax4,
                                    cmap='viridis', scheme='equal_interval', k=11)
            
            # BIOSAFE score per taxonomic group
            PotTax_reference.plot.bar(ax=ax5)
            ax5.set_ylim(0,37)
            PotTax_intervention.plot.bar(ax=ax6)
            ax6.set_ylim(0,37)
            
            #plt.savefig('biosafe_comparison.png', dpi=300)
        return


def main():
    biosafe = BiosafeVR()


if __name__ == "__main__":
    main()
