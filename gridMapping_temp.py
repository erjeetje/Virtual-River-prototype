# -*- coding: utf-8 -*-
"""
Created on Thu Feb 28 16:07:11 2019

@author: HaanRJ
"""

import time
import json
import cv2
import geojson
import numpy as np
import netCDF4
import bmi.wrapper
import matplotlib.pyplot as plt
from copy import deepcopy
from scipy.spatial import cKDTree
from shapely import geometry
from shapely.ops import unary_union
from rasterio import open as opentif
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.crs import CRS
from PIL import Image
from io import BytesIO


def read_calibration():
    """
    function that loads and returns the calibration. Currently not called in
    the control script as calibration transforms are stored internally.
    """
    with open('calibration.json') as f:
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


def read_hexagons(filename='hexagons1.geojson'):
    """
    function that loads and returns the hexagons. Currently not called in
    the control script as the hexagons are stored internally.
    """
    with open(filename) as f:
        features = geojson.load(f)
    return features


def read_node_grid(save=False):
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
        with open('grid.geojson', 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def read_face_grid(model, save=False):
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
        with open('face_grid.geojson', 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def hexagons_to_fill(hexagons):
    dikes_top = []
    dikes_bottom = []
    for feature in hexagons.features:
        if feature.properties["z"] >= 4:
            shape = geometry.asShape(feature.geometry)
            y_hex = shape.centroid.y
            if y_hex >= 0:
                dikes_top.append(feature)
            else:
                dikes_bottom.append(feature)
    dikes_top = geojson.FeatureCollection(dikes_top)
    dikes_bottom = geojson.FeatureCollection(dikes_bottom)

    for feature in hexagons.features:
        try:
            dike_top = dikes_top[feature.properties["column"]-1]
        except KeyError:
            print("area does not have a complete dike in the north")
            continue
        try:
            dike_bottom = dikes_bottom[feature.properties["column"]-1]
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

    # determine whether or not a point in the grid falls inside or outside.
    # of the board bbox.
    inside_id = []
    inside_coor = []
    """
    border_id = []
    border_coor = []
    """
    x_coor = np.array([feature.geometry['coordinates'][0] for feature in grid['features']])
    x_min = min(x_coor)
    x_max = max(x_coor)
    """
    y_coor = np.array([feature.geometry['coordinates'][1] for feature in grid['features']])
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
            feature.properties["nearest"] = [inside_id[indices1], border_id[indices2]]
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
            if feature.properties["behind_dike"]:
                indices_updated.append(feature.id)
        else:
            if feature.properties["changed"]:
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


def interpolate_node_grid(hexagons, grid, turn=0, save=False):
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
        with open(filename, 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def create_geotiff(grid, turn=0):
    """
    Function that creates a GeoTIFF from the grid as constructed in the
    hex_to_points function
    """
    d = turn
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
    out = np.array([feature.properties['z'] for feature in features['features']])
    img = rasterize(zip(geometries, out), out_shape=(750, 1000))
    img = cv2.flip(img, 0)
    plt.imshow(img)

    compression = {"compress": "LZW"}
    with opentif('grid_height_map%d.tif'%d, 'w', driver='GTiff', width=1000,
                 height=750, count=1, dtype=img.dtype, crs='EPSG:3857',
                 transform=from_origin(0, 0, 1, 1), **compression) as dst:
        dst.write(img, 1)
    return


def run_model(grid, hexagons):
    model = bmi.wrapper.BMIWrapper('dflowfm')
    model.initialize(r'C:\Users\HaanRJ\Documents\GitHub\sandbox-fm\models\sandbox\Waal_schematic\waal_with_side.mdu')
    print('model initialized')
    face_grid = read_face_grid(model)
    print(model.get_current_time())
    model.get_var('s1')
    #numk = model.get_var('numk')
    #ndx = model.get_var('ndx')
    ndxi = model.get_var('ndxi')

    # points, nodes, vertices (corner points)
    xk = model.get_var('xk')
    yk = model.get_var('yk')

    # cell centers
    xzw = model.get_var('xzw')
    yzw = model.get_var('yzw')

    # on the nodes
    zk = model.get_var('zk')

    # on the faces/cells (including boundary points)
    s1 = model.get_var('s1')[:ndxi]
    ucx = model.get_var('ucx')[:ndxi]
    ucy = model.get_var('ucy')[:ndxi]

    s1_t0 = s1.copy()
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
    sc = axes[0].scatter(xzw, yzw, c=s1, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    sc_zk = axes[1].scatter(xk, yk, c=zk, edgecolor='none', vmin=0, vmax=6, cmap='jet')

    plt.show()
    zk_new = np.array([feature.properties['z'] for feature in grid['features']])
    for i in range(10):
        model.update()
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(s1.copy())
        sc_zk.set_array(zk.copy())
        plt.draw()
        plt.pause(0.00001)
    qv = axes[1].quiver(xzw, yzw, ucx, ucy)
    changed = [
            feature
            for feature
            in grid.features
            if feature.properties['changed']
    ]
    frcu = model.get_var('frcu')
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    default_landuse = 8
    for feature in node_grid.features:
        feature.properties["landuse"] = default_landuse
        if not feature.properties["board"]:
            continue
        try:
            location = feature.properties["nearest"][0]
        except TypeError:
            location = feature.properties["nearest"]
        hexagon = hexagons_by_id[location]
        landuse = hexagon.properties["landuse"]
        # for now use z
        if hexagon.properties['z'] == 0:
            landuse = 9
        else:
            landuse = 8
        feature.properties["landuse"] = landuse
    for feature in node_grid.features:
        friction = landuse_to_friction(feature.properties['landuse'])
        frcu[feature.id] = friction
    if False:
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64') * 1.5
            model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
            )
    s0 = s1.copy()
    model.update(60)
    for i in range(50):
        model.update(3)
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(s1.copy() - s0)
        sc_zk.set_array(zk.copy())
        qv.set_UVC(ucx.copy(), ucy.copy())
        plt.draw()
        plt.pause(0.00001)

    print(model.get_current_time())


def landuse_to_friction(landuse):
    if landuse == 9:
        friction = 1000
    else:
        friction = 1
    return friction


if __name__ == "__main__":
    save = False
    turn = 0
    plt.interactive(True)
    calibration = read_calibration()
    t0 = time.time()
    hexagons = read_hexagons(filename='hexagons0.geojson')
    t1 = time.time()
    print("Read hexagons: " + str(t1 - t0))
    node_grid = read_node_grid()
    t2 = time.time()
    print("Load grid: " + str(t2 - t1))
    node_grid = index_node_grid(hexagons, node_grid)
    t3 = time.time()
    print("Index grid: " + str(t3 - t2))
    node_grid = interpolate_node_grid(hexagons, node_grid)
    with open('node_grid_before%d.geojson' % turn, 'w') as f:
        geojson.dump(node_grid, f, sort_keys=True,
                     indent=2)
    t4 = time.time()
    print("Interpolate grid: " + str(t4 - t3))
    filled_node_grid = deepcopy(node_grid)
    filled_hexagons = deepcopy(hexagons)
    filled_hexagons = hexagons_to_fill(filled_hexagons)
    t5 = time.time()
    print("Hexagons to fill: " + str(t5 - t4))
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
    create_geotiff(node_grid)
    t9 = time.time()
    print("Created geotiff: " + str(t9 - t8))
    #run_model(filled_node_grid, hexagons)