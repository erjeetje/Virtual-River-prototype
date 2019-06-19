# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 11:31:30 2019

@author: HaanRJ
"""

import time
import os
import json
#import cv2
import geojson
import numpy as np
import netCDF4
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import modelInterface as D3D
import updateRoughness as roughness
import createStructures as structures
from copy import deepcopy
from scipy.spatial import cKDTree
from scipy import interpolate
from shapely import geometry
from shapely.ops import unary_union
from rasterio import open as opentif
from rasterio.features import rasterize
from rasterio.transform import from_origin
from scipy.ndimage.filters import gaussian_filter