# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""



class costModule():
    def __init__(self):
        super(costModule, self).__init__()
        acqi_m2 = {
                "agriculture": 6.7,
                "nature": 1.2,
                "water": 0.8,
                "build_envi": 190
                }
        acqi_type = {
                "house": 500000,
                "farm": 900000,
                "business": 1400000
                }
        demo_type = {
                "house": 20000,
                "farm": 40000,
                "business": 120000
                }
        floodplain_lowering_m2 = {
                "storage": 7.2,
                "polluted": 10.2,
                "local_use": 3.1
                }
        sidechannel_m2 = {
                "storage": 8.1,
                "polluted": 10.2,
                "local_use": 3.1
                }
        minor_embankment_m2 = {
                "storage": 6.9,
                "polluted": 10.2,
                "local_use": 3.1
                }
        roughness_smooth_m2 = {
                "grass": 0.054,
                "herbaceous": 0.081,
                "forest": 0.133
                }
        structures_m = {
                "lower": 650,
                "ltd": 1900
                }