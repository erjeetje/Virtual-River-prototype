# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 17:08:52 2019

@author: HaanRJ
"""

def construct_road(dike):
    x_coor = []
    y_coor = []
    for feature in dike.features:
        shape = geometry.asShape(feature.geometry)
        x = shape.centroid.x
        y = shape.centroid.y
        x_coor.append(x)
        y_coor.append(y)
    x_coor = np.array(x_coor)
    y_coor = np.array(y_coor)
    tck = interpolate.splrep(x, y, s=0)
    xnew = np.linspace(1, 1000, 100)
    ynew = interpolate.splev(xnew, tck, der=0)
    ytop = ynew + 5
    ybottom = ynew - 5
    return