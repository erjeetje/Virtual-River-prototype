# -*- coding: utf-8 -*-
"""
Created on Thu Feb 28 16:07:11 2019

@author: HaanRJ
"""


import time
import os
import json
import cv2
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


def read_calibration(path=""):
    """
    function that loads and returns the calibration. Currently not called in
    the control script as calibration transforms are stored internally.
    """
    with open(os.path.join(path, 'calibration.json')) as f:
        calibration = json.load(f)
    # convert to transform matrix
    sandbox_transform = cv2.getPerspectiveTransform(
            np.array(calibration['img_post_cut_points'], dtype='float32'),
            np.array(calibration['model_points'], dtype='float32')
    )
    tygron_transform = cv2.getPerspectiveTransform(
            np.array(calibration['img_post_cut_points'], dtype='float32'),
            np.array(calibration['tygron_export'], dtype='float32')
    )
    calibration['image_post_cut2model'] = sandbox_transform
    calibration['image_post_cut2tygron'] = tygron_transform
    return calibration


def read_hexagons(filename='hexagons1.geojson', path=""):
    """
    function that loads and returns the hexagons. Currently not called in
    the control script as the hexagons are stored internally.
    """
    with open(os.path.join(path, filename)) as f:
        features = geojson.load(f)
    return features


def read_node_grid(save=False, path=""):
    """
    function that loads and returns the grid.
    """
    loc = r"D:\Werkzaamheden map\Onderzoek\Design 2018\Models\300x200_2_net.nc"
    ds = netCDF4.Dataset(loc)
    x = ds.variables['NetNode_x'][:]
    y = ds.variables['NetNode_y'][:]
    ds.close()

    xy = np.c_[x, y]
    features = []
    for i, xy_i in enumerate(xy):
        pt = geojson.Point(coordinates=list(xy_i))
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open(os.path.join(path, 'node_grid.geojson'), 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def read_face_grid(model, save=False, path=""):
    """
    function that loads and returns the grid.
    """
    x = model.get_var('xzw')
    y = model.get_var('yzw')
    xy = np.c_[x, y]
    features = []
    for i, xy_i in enumerate(xy):
        pt = geojson.Point(coordinates=list(xy_i))
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open(os.path.join(path, 'face_grid.geojson'), 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def hexagons_to_fill(hexagons):
    dikes_north = []
    dikes_south = []
    for feature in hexagons.features:
        if feature.properties["north_dike"] is True:
            dikes_north.append(feature)
        elif feature.properties["south_dike"] is True:
            dikes_south.append(feature)
    dikes_north = geojson.FeatureCollection(dikes_north)
    dikes_south = geojson.FeatureCollection(dikes_south)

    for feature in hexagons.features:
        try:
            dike_top = dikes_north[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a complete dike in the north")
            continue
        try:
            dike_bottom = dikes_south[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a complete dike in the south")
            continue
        if feature.id < dike_top.id:
            feature.properties["behind_dike"] = True
            feature.properties["z"] = dike_top.properties["z"]
        elif feature.id > dike_bottom.id:
            feature.properties["behind_dike"] = True
            feature.properties["z"] = dike_bottom.properties["z"]
        else:
            feature.properties["behind_dike"] = False
    return hexagons


def index_face_grid(hexagons, grid):
    hex_coor = []
    polygons = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    line = list(geojson.utils.coords(board_feature))
    minx = 0.0
    miny = 0.0
    maxx = 0.0
    maxy = 0.0
    for x, y in line:
        if x < minx:
            minx = x
        elif x > maxx:
            maxx = x
        else:
            continue
        if y < miny:
            miny = y
        elif y > maxy:
            maxy = y
        else:
            continue
    bbox = geometry.Polygon([(minx, maxy), (maxx, maxy), (maxx, miny),
                             (minx, miny), (minx, maxy)])
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        x_point = point.centroid.x
        y_point = point.centroid.y
        xy = np.array([x_point, y_point])
        if bbox.contains(point):
            feature.properties["board"] = True
            dist, index = hex_locations.query(xy)
            feature.properties["location"] = index
            feature.properties["changed"] = True
        else:
            feature.properties["board"] = False
            feature.properties["location"] = None
            feature.properties["changed"] = True
    return grid


def index_node_grid(hexagons, grid):
    hex_coor = []
    polygons = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    """
    board_featurecollection = geojson.FeatureCollection([board_feature])
    with open('board_border.geojson', 'w') as f:
        geojson.dump(board_featurecollection, f, sort_keys=True, indent=2)
    """
    line = list(geojson.utils.coords(board_feature))

    # determine the bounding box coordinates of the board.
    minx = 0.0
    miny = 0.0
    maxx = 0.0
    maxy = 0.0
    for x, y in line:
        if x < minx:
            minx = x
        elif x > maxx:
            maxx = x
        if y < miny:
            miny = y
        elif y > maxy:
            maxy = y
    bbox = geometry.Polygon([(minx, maxy), (maxx, maxy), (maxx, miny),
                             (minx, miny), (minx, maxy)])

    # determine whether or not a point in the grid falls inside or outside.
    # of the board bbox.
    inside_id = []
    inside_coor = []
    """
    border_id = []
    border_coor = []
    """
    x_coor = np.array([feature.geometry['coordinates'][0] for
                       feature in grid['features']])
    x_min = min(x_coor)
    x_max = max(x_coor)
    """
    y_coor = np.array([feature.geometry['coordinates'][1] for
                       feature in grid['features']])
    y_coor = np.unique(y_coor)
    if y_coor[0] > 0:
        y_step = y_coor[0] - y_coor[1]
    else:    
        y_step = y_coor[1] - y_coor[0]
    y_z = np.full(len(y_coor), 4.0)
    for i, y in enumerate(y_coor):
        if y > (maxy-10*y_step) or y < (miny+10*y_step):
            continue
        # dike to floodplain
        if (y < (maxy-10*y_step) and y > (maxy-11*y_step)) or (y > (miny+10*y_step) and y < (miny+11*y_step)):
            y_z[i] = 3.9
        elif (y < (maxy-11*y_step) and y > (maxy-12*y_step)) or (y > (miny+11*y_step) and y < (miny+12*y_step)):
            y_z[i] = 3.7
        elif (y < (maxy-12*y_step) and y > (maxy-13*y_step)) or (y > (miny+12*y_step) and y < (miny+13*y_step)):
            y_z[i] = 3.4
        elif (y < (maxy-13*y_step) and y > (maxy-14*y_step)) or (y > (miny+13*y_step) and y < (miny+14*y_step)):
            y_z[i] = 3
        elif (y < (maxy-14*y_step) and y > (maxy-15*y_step)) or (y > (miny+14*y_step) and y < (miny+15*y_step)):
            y_z[i] = 2.6
        elif (y < (maxy-15*y_step) and y > (maxy-16*y_step)) or (y > (miny+15*y_step) and y < (miny+16*y_step)):
            y_z[i] = 2.3
        elif (y < (maxy-16*y_step) and y > (maxy-17*y_step)) or (y > (miny+16*y_step) and y < (miny+17*y_step)):
            y_z[i] = 2.1
        # river bed
        elif y < (10*y_step) and y > (10*-y_step):
            y_z[i] = 0
        elif (y < (11*y_step) and y > (10*y_step)) or (y > (11*-y_step) and y < (10*-y_step)):
            y_z[i] = 0.1
        elif (y < (12*y_step) and y > (11*y_step)) or (y > (12*-y_step) and y < (11*-y_step)):
            y_z[i] = 0.3
        elif (y < (13*y_step) and y > (12*y_step)) or (y > (13*-y_step) and y < (12*-y_step)):
            y_z[i] = 0.6
        elif (y < (14*y_step) and y > (13*y_step)) or (y > (14*-y_step) and y < (13*-y_step)):
            y_z[i] = 1
        elif (y < (15*y_step) and y > (14*y_step)) or (y > (15*-y_step) and y < (14*-y_step)):
            y_z[i] = 1.4
        elif (y < (16*y_step) and y > (15*y_step)) or (y > (16*-y_step) and y < (15*-y_step)):
            y_z[i] = 1.7
        elif (y < (17*y_step) and y > (16*y_step)) or (y > (17*-y_step) and y < (16*-y_step)):
            y_z[i] = 1.9
        else:
            y_z[i] = 2
    border_values = np.array(list(zip(y_coor, y_z)))
    """
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        x_point = point.centroid.x
        y_point = point.centroid.y
        if not bbox.contains(point):
            feature.properties["board"] = False
            feature.properties["border"] = False
            feature.properties["changed"] = True
            feature.properties["fill"] = False
            if y_point > maxy or y_point < miny:
                feature.properties["fill"] = True
                feature.properties["z"] = 4.0
            elif x_point == x_min or x_point == x_max:
                feature.properties["border"] = True
                """
                index = np.where(border_values[:, 0] == y_point)
                feature.properties["z"] = float(border_values[index, 1])
                """
                """
                border_id.append(feature.id)
                border_coor.append([x_point, y_point])
                """
        else:  
            feature.properties["board"] = True
            feature.properties["border"] = False
            feature.properties["changed"] = True
            feature.properties["fill"] = False
            inside_id.append(feature.id)
            inside_coor.append([x_point, y_point])

    # create a cKDTree of all the points that fall within the board bbox.
    inside_coor = np.array(inside_coor)
    inside_locations = cKDTree(inside_coor)
    """
    border_coor = np.array(border_coor)
    border_locations = cKDTree(border_coor)
    """

    # index the all the grid points to either up to the nearest three
    # hexagons in case the grid point falls within the board bbox.
    # Weighting factors are stored in case two or three hexagons are
    # indexed that can be accessed in case one or more of these hexagons
    # change after a board state update. Otherwise index the grid point to
    # the closest neighbour that falls within the board bbox.
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])

        # the block of code below specifies the rules on how many hexagons
        # are indixed for each point that is positioned within the game
        # board, based on the location of each point and the distance to
        # the nearest three hexagons.

        # afvangen dist[x] = 0.0
        if feature.properties["board"]:
            dist, indices = hex_locations.query(xy, k=3)
            feature.properties["location"] = indices[0].tolist()
            if dist[0] > 35:
                if dist[1] <= 60:
                    if dist[2] <= 60:
                        weights = 1 / np.power(dist, 2)
                        weights_sum = sum(weights)
                        feature.properties["nearest"] = indices.tolist()
                        feature.properties["weight"] = weights.tolist()
                        feature.properties["weight_sum"] = weights_sum
                    else:
                        weights = 1 / np.power(dist[0:2], 2)
                        weights_sum = sum(weights)
                        feature.properties["nearest"] = indices[0:2].tolist()
                        feature.properties["weight"] = weights.tolist()
                        feature.properties["weight_sum"] = weights_sum
                else:
                    feature.properties["nearest"] = indices[0].tolist()
            elif dist[1] > 45:
                feature.properties["nearest"] = indices[0].tolist()
            elif dist[2] > 45:
                weights = 1 / np.power(dist[0:2], 2)
                weights_sum = sum(weights)
                feature.properties["nearest"] = indices[0:2].tolist()
                feature.properties["weight"] = weights.tolist()
                feature.properties["weight_sum"] = weights_sum
            else:
                weights = 1 / np.power(dist, 2)
                weights_sum = sum(weights)
                feature.properties["nearest"] = indices.tolist()
                feature.properties["weight"] = weights.tolist()
                feature.properties["weight_sum"] = weights_sum
        # if the grid point is not within the board bbox, index to the
        # nearest grid point that is on located within the board bbox.
        #elif feature.properties["border"]:
        else:
            dist, indices = inside_locations.query(xy)
            feature.properties["location"] = None
            feature.properties["nearest"] = inside_id[indices]
        """
        else:
            dist1, indices1 = inside_locations.query(xy)
            dist2, indices2 = border_locations.query(xy)
            #weights = 1 / np.power([dist1, dist2], 2)
            weights = [1 / dist1, 1 / dist2]
            weights_sum = sum(weights)
            feature.properties["nearest"] = [inside_id[indices1],
                                             border_id[indices2]]
            feature.properties["weight"] = weights
            feature.properties["weight_sum"] = weights_sum
        """

        # change this section to finding the nearest neighbour on the
        # horizontal axis + another rule if no nearest neighbour on the
        # horizontal axis
    return grid


def update_node_grid(hexagons, grid, fill=False, turn=0):
    # In case the method is called as an update, determine which grid
    # points require updating based on which hexagons are changed. This
    # way, only the grid points that need updating are updated, speeding
    # up the updating process.
    indices_updated = []
    counter = 0
    for feature in hexagons.features:
        if fill:
            if feature.properties["behind_dike"] or \
                    feature.properties["z_changed"]:
                indices_updated.append(feature.id)
        else:
            if feature.properties["z_changed"]:
                indices_updated.append(feature.id)
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        if type(feature.properties["nearest"]) is int:
            if feature.properties["nearest"] in indices_updated:
                feature.properties["changed"] = True
                counter += 1
            else:
                feature.properties["changed"] = False
        elif any((True for x in feature.properties["nearest"]
                  if x in indices_updated)):
            feature.properties["changed"] = True
            counter += 1
        else:
            feature.properties["changed"] = False
    print("Hexagons updated are: "+str(indices_updated))
    print("Number of gridpoints inside the board to update: "+str(counter))
    return grid


def interpolate_node_grid(hexagons, grid, turn=0, save=False, path=""):
    # block of code that calculates the z variable for each grid point, based
    # on stored indices and, if applicable, weight factors. Distinguishes
    # between start (updates all as all are changed) and update (updates only
    # points connected to changed hexagons).
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        if not feature.properties["changed"]:
            continue
        nearest = feature.properties["nearest"]
        if type(nearest) is int:
            hexagon = hexagons_by_id[nearest]
            feature.properties['z'] = hexagon.properties['z']
            continue
        if len(nearest) == 2:
            weights = feature.properties["weight"]
            weights_sum = feature.properties["weight_sum"]
            hexagon1 = hexagons_by_id[nearest[0]]
            hexagon2 = hexagons_by_id[nearest[1]]
            feature.properties['z'] = \
                round(hexagon1.properties['z'] * (weights[0] /
                      weights_sum) + hexagon2.properties['z'] *
                      (weights[1] / weights_sum), 5)
        else:
            weights = feature.properties["weight"]
            weights_sum = feature.properties["weight_sum"]
            hexagon1 = hexagons_by_id[nearest[0]]
            hexagon2 = hexagons_by_id[nearest[1]]
            hexagon3 = hexagons_by_id[nearest[2]]
            feature.properties['z'] = \
                round(hexagon1.properties['z'] * (weights[0] /
                      weights_sum) + hexagon2.properties['z'] *
                      (weights[1] / weights_sum) +
                      hexagon3.properties['z'] * (weights[2] /
                      weights_sum), 5)

    # block of code that sets the z variable for each grid point outside of the
    # game board by setting the z value equal to the z value of the nearest
    # grid point on the board.
    grid_by_id = {feature.id: feature for feature in grid.features}
    counter = 0
    for feature in grid.features:
        if feature.properties["board"] or feature.properties["fill"]:
            continue
        nearest = feature.properties["nearest"]
        inside_point = grid_by_id[nearest]
        feature.properties["z"] = inside_point.properties["z"]
        """
        inside_point1 = grid_by_id[nearest[0]]
        inside_point2 = grid_by_id[nearest[1]]
        if inside_point1.properties["changed"] or inside_point2.properties["changed"]:
            weights = feature.properties["weight"]
            weights_sum = feature.properties["weight_sum"]
            feature.properties['z'] = \
                round(inside_point1.properties['z'] * (weights[0] /
                      weights_sum) + inside_point2.properties['z'] *
                      (weights[1] / weights_sum), 5)
        """
    if turn != 0:
        print("Number of gridpoints outside the board updated: "+str(counter))
    if save:
        filename = 'interpolated_grid%d.geojson' % turn
        with open(os.path.join(path, filename), 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def create_geotiff(grid, turn=0, path="", save=False):
    """
    Function that creates a GeoTIFF from the grid as constructed in the
    hex_to_points function, using interpolation to smoothen the heightmap.
    """
    x_coor = []
    y_coor = []
    data = []
    step = 3 * 1.25
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x = (shape.centroid.x + 400) * 1.25
        y = (shape.centroid.y + 300) * 1.25
        if x < (0 - step) or x > (1000 + step):
            continue
        if y < (0 - step) or y > (750 + step):
            continue
        x_coor.append(x)
        y_coor.append(y)
        """
        The code below can be adjusted to 'manipulate' how the virtual world
        will look in Tygron. Current implementation amplifies the dike segments
        """
        height = (feature.properties["z"] * 4) - 6
        if height > 8:
            height = height * 1.5
        data.append(height)
    x_coor = np.array(x_coor)
    y_coor = np.array(y_coor)
    data = np.array(data)
    xvalues = np.linspace(1, 1000, 1000)
    yvalues = np.linspace(1, 750, 750)
    xx, yy = np.meshgrid(xvalues, yvalues)
    interpolated_data = interpolate.griddata((x_coor, y_coor), data, (xx, yy))
    interpolated_data = cv2.flip(interpolated_data, 0)
    if save:
        with open('interpolated_data.csv', 'w') as f:
            for line in interpolated_data:
                f.write(str(line))
                f.write('\n')
    """
    min_data = min(data)
    max_data = max(data)
    create_heatmap(interpolated_data, min_data, max_data, name="Elevation_plot", cmap="gist_earth", sigma=(5, 5, 1))
    """

    compression = {"compress": "LZW"}
    filename = 'grid_height_map%d.tif' % turn
    with opentif(os.path.join(path, filename), 'w',
                 driver='GTiff', width=1000, height=750, count=1,
                 dtype=interpolated_data.dtype, crs='EPSG:3857',
                 transform=from_origin(0, 0, 1, 1), **compression) as dst:
        dst.write(interpolated_data, 1)
    """
    To do: return img directly instead of saving, if possible (changing it to
    raster and then to string is possible, but adding crs may be a challenge).
    """
    return interpolated_data


def create_geotiff_old(grid, turn=0, path=""):
    """
    Function that creates a GeoTIFF from the grid as constructed in the
    hex_to_points function
    """
    tic = time.time()
    features = []
    step = 3 * 1.25
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x = (shape.centroid.x + 400) * 1.25
        y = (shape.centroid.y + 300) * 1.25
        if x < (0 - step) or x > (1000 + step):
            continue
        if y < (0 - step) or y > (750 + step):
            continue
        point1 = [x-step, y+step]
        point2 = [x+step, y+step]
        point3 = [x+step, y-step]
        point4 = [x-step, y-step]
        polygon = geojson.Polygon([[point1, point2, point3, point4, point1]])
        new_feature = geojson.Feature(geometry=polygon)
        # adjustment of z value to meters that range from -6m to 14m
        new_feature.properties['z'] = (feature.properties['z'] * 4) - 6
        features.append(new_feature)
    features = geojson.FeatureCollection(features)
    geometries = [feature.geometry for feature in features.features]
    out = np.array([feature.properties['z'] for
                    feature in features['features']])
    heightmap = rasterize(zip(geometries, out), out_shape=(750, 1000))
    heightmap = cv2.flip(heightmap, 0)
    #plt.imshow(heightmap)

    compression = {"compress": "LZW"}
    with opentif(os.path.join(path, 'grid_height_map%d.tif' % turn), 'w',
                 driver='GTiff', width=1000, height=750, count=1,
                 dtype=heightmap.dtype, crs='EPSG:3857',
                 transform=from_origin(0, 0, 1, 1), **compression) as dst:
        dst.write(heightmap, 1)
    """
    To do: return img directly instead of saving
    """
    tac = time.time()
    print(tac-tic)
    return heightmap


def create_roughness_map(grid, turn=0, path="", save=False):
    x_coor = []
    y_coor = []
    data = []
    step = 3 * 1.25
    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x = (shape.centroid.x + 400) * 1.25
        y = (shape.centroid.y + 300) * 1.25
        if x < (0 - step) or x > (1000 + step):
            continue
        if y < (0 - step) or y > (750 + step):
            continue
        x_coor.append(x)
        y_coor.append(y)
        try:
            chezy = feature.properties["Chezy"]
        except KeyError:
            chezy = 45.0
        data.append(chezy)
    x_coor = np.array(x_coor)
    y_coor = np.array(y_coor)
    data = np.array(data)
    xvalues = np.linspace(1, 1000, 1000)
    yvalues = np.linspace(1, 750, 750)
    xx, yy = np.meshgrid(xvalues, yvalues)
    interpolated_data = interpolate.griddata((x_coor, y_coor), data, (xx, yy))
    interpolated_data = cv2.flip(interpolated_data, 0)
    #cv2.imshow('raw', np.uint8(interpolated_data * 256)[...,:3])
    #cv2.imshow('heatmap', interpolated_data)
    #heatmap = gaussian_filter(interpolated_data, sigma=1)
    #heatmap = cv2.GaussianBlur(interpolated_data,(505,505),cv2.BORDER_DEFAULT)
    #plt.imshow(interpolated_data)
    #print(interpolated_data.dtype)
    """
    max_data = max(data)
    min_data = min(data)
    create_heatmap(interpolated_data, min_data, max_data, name="Chezy_plot", cmap="viridis", sigma=(16, 16, 1))
    """
    return interpolated_data


def create_heatmap(data, min_data, max_data, name="plot", cmap="viridis", sigma=(16, 16, 1)):
    """
    This function is here temporarily. Should be handled by the vizualization module.
    """
    N = colors.Normalize(min_data, max_data)
    cmap = getattr(plt.cm, cmap)
    rgba = cmap(N(data))
    heatmap_scipy = gaussian_filter(rgba, sigma=sigma)
    kernel = sigma[0] * 8 * 4 + 1
    heatmap_opencv = cv2.GaussianBlur(rgba, (kernel, kernel), cv2.BORDER_DEFAULT)
    #correction = 255 / max_data
    rgb = np.uint8(rgba * 256)[...,:3]
    heatmap_scipy_rgb = np.uint8(heatmap_scipy * 256)[...,:3]
    heatmap_opencv_rgb = np.uint8(heatmap_opencv * 256)[...,:3]
    heatmap_scipy_name = (name + "scipy_heatmap")
    heatmap_opencv_name = (name + "opencv_heatmap")
    cv2.imwrite((name + '.jpg'), rgb)
    cv2.imwrite((heatmap_scipy_name + '.jpg'), heatmap_scipy_rgb)
    cv2.imwrite((heatmap_opencv_name + '.jpg'), heatmap_opencv_rgb)
    cv2.imshow(name, rgb)
    cv2.imshow(heatmap_scipy_name, heatmap_scipy_rgb)
    cv2.imshow(heatmap_opencv_name, heatmap_opencv_rgb)
    return


if __name__ == "__main__":
    save = False
    turn = 0
    plt.interactive(True)
    calibration = read_calibration()
    t0 = time.time()
    hexagons = read_hexagons(filename='hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
    hexagons = structures.determine_dikes(hexagons)
    hexagons = structures.determine_channel(hexagons)
    t1 = time.time()
    print("Read hexagons: " + str(t1 - t0))
    node_grid = read_node_grid()
    model = D3D.initialize_model()
    face_grid = read_face_grid(model)
    t2 = time.time()
    print("Load node and face grids: " + str(t2 - t1))
    node_grid = index_node_grid(hexagons, node_grid)
    face_grid = index_face_grid(hexagons, face_grid)
    t3 = time.time()
    print("Index node and face grid: " + str(t3 - t2))
    node_grid = interpolate_node_grid(hexagons, node_grid)
    hexagons, face_grid = roughness.hex_to_points(model, hexagons, face_grid)
    with open('node_grid_before%d.geojson' % turn, 'w') as f:
        geojson.dump(node_grid, f, sort_keys=True,
                     indent=2)
    with open('face_grid_vegetation.geojson', 'w') as f:
        geojson.dump(face_grid, f, sort_keys=True, indent=2)
    t4 = time.time()
    print("Interpolate grid: " + str(t4 - t3))
    filled_node_grid = deepcopy(node_grid)
    filled_hexagons = deepcopy(hexagons)
    filled_hexagons = hexagons_to_fill(filled_hexagons)
    t5 = time.time()
    print("Hexagons to fill: " + str(t5 - t4))
    test_print = []
    filled_node_grid = update_node_grid(filled_hexagons, filled_node_grid,
                                        fill=True)
    t6 = time.time()
    print("Nodes to fill: " + str(t6 - t5))
    filled_node_grid = interpolate_node_grid(filled_hexagons, filled_node_grid,
                                             turn=turn)
    t7 = time.time()
    print("Interpolated filled grid: " + str(t7 - t6))
    if save:
        with open('node_grid_after%d.geojson' % turn, 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open('filled_node_grid%d.geojson' % turn, 'w') as f:
            geojson.dump(filled_node_grid, f, sort_keys=True,
                         indent=2)
    t8 = time.time()
    if save:
        print("Saved both grids: " + str(t8 - t7))
    heightmap = create_geotiff(node_grid)
    heatmap = create_roughness_map(face_grid)
    t9 = time.time()
    print("Created geotiff: " + str(t9 - t8))
    #D3D.run_model(model, filled_node_grid, face_grid, hexagons)
    """
    with open('node_grid0.geojson', 'r') as f:
        grid = geojson.load(f)
    heightmap = create_geotiff(grid)
    tygron.set_elevation(heightmap)
    """
    if save:
        with open('hexagons_visualization_test.geojson', 'w') as f:
            geojson.dump(hexagons, f, sort_keys=True,
                         indent=2)
        with open('node_grid_visualization_test.geojson', 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open('face_grid_visualization_test.geojson', 'w') as f:
            geojson.dump(face_grid, f, sort_keys=True,
                         indent=2)
        print("saved files")
