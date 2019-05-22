# -*- coding: utf-8 -*-
"""
Created on Tue May 21 16:52:46 2019

@author: HaanRJ
"""
import bmi.wrapper
if __name__ == '__main__':
    model = bmi.wrapper.BMIWrapper('dflowfm')
    model.initialize(r'C:/Users/HaanRJ/Documents/GitHub/sandbox-fm/models/sandbox/c080_critical_flow_over_subgrid_weir/weir01_Q-H.mdu')
    model.library.get_compound_field('weirs', 'FixedWeir01', 'crest_level')
