# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:56:30 2019

@author: straa005
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import biosafe as bsf

def pjoin(in_dir, file_name):
    return os.path.join(in_dir, file_name)

def ecotope_area_sums(board, vr_ecotopes):
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
    board_eco = pd.merge(board_clean, vr_ecotopes,
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

#%% Main

# Directory settings
root_dir = os.path.dirname(os.path.realpath(__file__))
#root_dir = os.path.dirname(os.getcwd())
scratch_dir = os.path.join(root_dir, 'scratch')
input_dir  = os.path.join(root_dir, 'input_data')
os.chdir(scratch_dir)

# Input data BIOSAFE
legal_weights = pd.read_csv(pjoin(input_dir, 'legalWeights.csv'), index_col = 0)
links_law = pd.read_csv(pjoin(input_dir, 'linksLaw.csv'), index_col = 0)
links_eco1 = pd.read_csv(pjoin(input_dir, 'linksEco.csv'), index_col = 0)
lut = pd.read_excel(pjoin(input_dir, 'BIOSAFE_20190711.xlsx'),
                     sheet_name = 'lut_RWES').fillna(method='ffill')
    # this lookup table (lut) has:
    #       ecotope codes of BIOSAFE in the first column: oldEcotope
    #       aggregated/translated ectotopes in the second column: newEcotope

# Input data Virtual River
board_reference = gpd.read_file(pjoin(input_dir, 'hexagons_biosafe1.geojson'))
board_intervention = gpd.read_file(pjoin(input_dir, 'hexagons_biosafe2.geojson'))
vr_eco = pd.read_csv(pjoin(input_dir, 'VR_ecotopes.csv'))

# Aggregate BIOSAFE ecotopes into RWES ecotopes
links_eco2 = bsf.aggregateEcotopes(links_eco1, lut)

# Generate dummy data in the right format
species_presence = pd.DataFrame(np.random.randint(2, size=len(links_law)),
                                columns=['speciesPresence'],
                                index=links_law.index)

ecotope_area = pd.DataFrame(np.ones(len(links_eco2.columns)-1) * 1e5,
                            columns = ['area_m2'],
                            index = links_eco2.columns.values[0:-1])

# Simplify ecotope tables to VR ecotopes
unique_eco = np.unique(np.hstack((vr_eco.ecotope1.values, vr_eco.ecotope2.values)))
links_eco3 = links_eco2.reindex(columns=unique_eco)
ecotope_area = ecotope_area.reindex(index=unique_eco)

# Run a first version of Biosafe
bsf_model = bsf.biosafe(legal_weights, links_law, links_eco3,
              species_presence, ecotope_area)

PotTax = bsf_model.TFI()
PotAll = bsf_model.FI()

# Evaluate board 1
eco_area_reference = ecotope_area_sums(board_reference, vr_eco)
bsf_model.ecotopeArea = eco_area_reference
PotTax_reference = bsf_model.TFI()
PotAll_reference = bsf_model.FI()
bsf.output2xlsx(bsf_model, 'bsf_reference.xlsx')

eco_area_intervention = ecotope_area_sums(board_intervention, vr_eco)
bsf_model.ecotopeArea = eco_area_intervention
PotTax_intervention = bsf_model.TFI()
PotAll_intervention = bsf_model.FI()
bsf.output2xlsx(bsf_model, 'bsf_intervention.xlsx')

#%% plot the data for checking
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

plt.savefig('biosafe_comparison.png', dpi=300)





























