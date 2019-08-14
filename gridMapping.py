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
    the main script as the hexagons are stored internally.
    """
    with open(os.path.join(path, filename)) as f:
        features = geojson.load(f)
    return features


def read_node_grid(save=False, path=""):
    """
    function that loads and returns the node grid (corners of the cells) from
    the netCDF file.
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


def create_flow_grid(model, save=False, path=""):
    ln = model.get_var('ln')
    x = model.get_var('xzw')
    y = model.get_var('yzw')
    flow_links = []
    skipped = 0
    for cells in ln:
        try:
            cell1_x = x[cells[0]-1]
            cell1_y = y[cells[0]-1]
            cell2_x = x[cells[1]-1]
            cell2_y = y[cells[1]-1]
            flow_x = (cell1_x + cell2_x) / 2.0
            flow_y = (cell1_y + cell2_y) / 2.0
            flow_links.append([flow_x, flow_y])
        except IndexError:
            skipped += 1
            continue
    print("NOTE:", str(skipped), "flow links skipped as unknown cells were",
          "called. Skipped cells are irrelevant for the board.")
    features = []
    for i, xy in enumerate(flow_links):
        pt = geojson.Point(coordinates=xy)
        feature = geojson.Feature(geometry=pt, id=i)
        features.append(feature)
    feature_collection = geojson.FeatureCollection(features)
    if save:
        with open(os.path.join(path, 'flowlinks_grid.geojson'), 'w') as f:
            geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def read_face_grid(model, save=False, path=""):
    """
    function that loads and returns the face grid (centers of the cells) from
    the model.
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
    """
    Functions that fills the hexagons behind the dike to the same height as the
    dike in the same column and on the same size (north or south). Uses the
    hexagon properties set in the createStructures script.
    """
    for feature in hexagons.features:
        if not feature.properties["behind_dike"]:
            continue
        else:
            dike = hexagons[feature.properties["dike_reference"]]
            feature.properties["z"] = dike.properties["z"]
    return hexagons


def hexagons_to_fill2(hexagons):
    """
    Functions that fills the hexagons behind the dike to the same height as the
    dike in the same column and on the same size (north or south). Uses the
    hexagon properties set in the createStructures script.
    """
    dikes_north = []
    dikes_south = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
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


def index_hexagons(hexagons, grid):
    grid_coor = []
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        x = point.centroid.x
        y = point.centroid.y
        grid_coor.append([x, y])
    grid_coor = np.array(grid_coor)
    grid_tree = cKDTree(grid_coor)
    for feature in hexagons.features:
        midpoint = geometry.asShape(feature.geometry)
        x = midpoint.centroid.x
        y = midpoint.centroid.y
        xy = np.array([x, y])
        dist, index = grid_tree.query(xy)
        feature.properties["face_cell"] = index
    return hexagons


def index_flow_grid(hexagons, grid):
    """
    Function that indexes the face grid to the hexagons. Determines in which
    hexagon a cell center is located.
    """
    hex_coor = []
    polygons = []
    # get x, y coordinates of each point and add it to hex_coor list to create
    # a cKDTree. Also add the shape of the hexagon to polygons to create a
    # single polygon of the game board.
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    # create cKDTree for indexing.
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    # create single polygon for the board.
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    # determine the bounding box of the board.
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
    # index the grid and add relevant properties to the grid features.
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
            feature.properties["fill"] = False
        else:
            if (y_point > maxy or y_point < miny):
                feature.properties["fill"] = True
                feature.properties["location"] = None
            else:
                feature.properties["fill"] = False
                dist, index = hex_locations.query(xy)
                feature.properties["location"] = index
            feature.properties["board"] = False
            feature.properties["changed"] = True
    return grid


def index_node_grid(hexagons, grid, slope):
    """
    Function that indexes the node grid to the hexagons. Determines the three
    closest hexagons to a point in the node grid. Also calculates weight
    factors based on the distance to the hexagon centers.
    """
    hex_coor = []
    polygons = []
    # get x, y coordinates of each point and add it to hex_coor list to create
    # a cKDTree. Also add the shape of the hexagon to polygons to create a
    # single polygon of the game board.
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    # create cKDTree for indexing.
    hex_coor = np.array(hex_coor)
    hex_locations = cKDTree(hex_coor)
    # create single polygon for the board.
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    if False:
        # save board feature. Currently skipped. May be removed later.
        board_featurecollection = geojson.FeatureCollection([board_feature])
        with open('board_border.geojson', 'w') as f:
            geojson.dump(board_featurecollection, f, sort_keys=True, indent=2)

    # determine the bounding box of the board.
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

    x_coor = np.array([feature.geometry['coordinates'][0] for
                       feature in grid['features']])
    x_min = min(x_coor)
    x_max = max(x_coor)
    # set properties for the grid point features position in relation to the
    # board. Points not in the board are not indexed later on and some other
    # values can be set immediately.
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        x_point = point.centroid.x
        y_point = point.centroid.y
        if not bbox.contains(point):
            feature.properties["board"] = False
            feature.properties["border"] = False
            feature.properties["changed"] = True
            feature.properties["fill"] = False
            if (y_point > maxy or y_point < miny):
                feature.properties["fill"] = True
                feature.properties["z"] = 16 + (abs(x_point - 600) * slope)
            elif (x_point == x_min or x_point == x_max):
                feature.properties["border"] = True
        else:  
            feature.properties["board"] = True
            feature.properties["border"] = False
            feature.properties["changed"] = True
            feature.properties["fill"] = False
            inside_id.append(feature.id)
            inside_coor.append([x_point, y_point])

    # create a cKDTree of all the points that fall within the board bbox. This
    # tree is used to index the points left and right of the board.
    inside_coor = np.array(inside_coor)
    inside_locations = cKDTree(inside_coor)

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
    return grid


def update_node_grid(hexagons, grid, fill=False, turn=0, printing=False, grid_type="node"):
    """ 
    Function to update the grid: determine which grid points require updating
    based on which hexagons are changed. This way, only the grid points that
    need updating are updated, speeding up the updating process.
    """
    indices_updated = []
    counter = 0
    # add feature ids of the changed hexagons to a list.
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            if not turn == 0:
                continue
        if fill:
            if (feature.properties["behind_dike"] or
                feature.properties["z_changed"]):
                indices_updated.append(feature.id)
        else:
            if feature.properties["z_changed"]:
                if (grid_type == "filled" and
                    feature.properties["behind_dike"]):
                        continue
                indices_updated.append(feature.id)
    # set the changed properties of the points in the grid indexed to a hexagon
    # indices_updated to True. Set the points that should not change to False.
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
    if printing:
        print("Hexagons updated are: "+str(indices_updated))
        print("Number of gridpoints inside the board to update: "+str(counter))
    return grid


def interpolate_node_grid(hexagons, grid, turn=0, fill=False, save=False,
                          path=""):
    """ 
    Function that calculates the z variable for each grid point, based
    on stored indices and, if applicable, weight factors. Distinguishes
    between start (updates all as all are changed) and update (updates only
    points connected to changed hexagons).
    """ 
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    # first interpolate the grid points that fall within the board.
    for feature in grid.features:
        if not feature.properties["board"]:
            continue
        # skip points that did not change.
        if not feature.properties["changed"]:
            continue
        nearest = feature.properties["nearest"]
        # interpolate z value for the point based on the indices and weight
        # factors.
        if type(nearest) is int:
            hexagon = hexagons_by_id[nearest]
            feature.properties["z"] = hexagon.properties["z"]
            continue
        if len(nearest) == 2:
            weights = feature.properties["weight"]
            weights_sum = feature.properties["weight_sum"]
            hexagon1 = hexagons_by_id[nearest[0]]
            hexagon2 = hexagons_by_id[nearest[1]]
            feature.properties["z"] = \
                round(hexagon1.properties["z"] * (weights[0] /
                      weights_sum) + hexagon2.properties["z"] *
                      (weights[1] / weights_sum), 5)
        else:
            weights = feature.properties["weight"]
            weights_sum = feature.properties["weight_sum"]
            hexagon1 = hexagons_by_id[nearest[0]]
            hexagon2 = hexagons_by_id[nearest[1]]
            hexagon3 = hexagons_by_id[nearest[2]]
            feature.properties["z"] = \
                round(hexagon1.properties["z"] * (weights[0] /
                      weights_sum) + hexagon2.properties["z"] *
                      (weights[1] / weights_sum) +
                      hexagon3.properties["z"] * (weights[2] /
                      weights_sum), 5)

    # block of code that sets the z variable for each grid point outside of the
    # game board by setting the z value equal to the z value of the nearest
    # grid point on the board.
    grid_by_id = {feature.id: feature for feature in grid.features}
    counter = 0
    for feature in grid.features:
        # skip the points within the board or that are filled by default.
        if feature.properties["board"] or feature.properties["fill"]:
            continue
        nearest = feature.properties["nearest"]
        inside_point = grid_by_id[nearest]
        feature.properties["z"] = inside_point.properties["z"]
    if (turn != 0 and not fill):
        print("Number of gridpoints outside the board updated: "+str(counter))
    if save:
        filename = 'interpolated_grid%d.geojson' % turn
        with open(os.path.join(path, filename), 'w') as f:
            geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def set_change_false(grid):
    for feature in grid.features:
        feature.properties["changed"] = False
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
        # some adjustments to place the bottom left of the board to
        # x, y = (0, 0)
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
        height = feature.properties["z"]
        if height > 14:
            height = height * 1.25
        data.append(height)
    x_coor = np.array(x_coor)
    y_coor = np.array(y_coor)
    data = np.array(data)
    # create a meshgrid of equal size of (x, y) as the desired geotiff
    xvalues = np.linspace(1, 1000, 1000)
    yvalues = np.linspace(1, 750, 750)
    xx, yy = np.meshgrid(xvalues, yvalues)
    # use scipys griddata function to interpolate for values at each point.
    interpolated_data = interpolate.griddata((x_coor, y_coor), data, (xx, yy))
    interpolated_data = cv2.flip(interpolated_data, 0)
    """
    min_data = min(data)
    max_data = max(data)
    create_heatmap(interpolated_data, min_data, max_data,
                   name="Elevation_plot", cmap="gist_earth", sigma=(5, 5, 1))
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
    raster and then to base64 string if possible, but adding crs may be a
    challenge).
    """
    return interpolated_data


def create_roughness_map(grid, turn=0, path="", save=False):
    """
    This function is here temporarily and should be seen as trial. Should be
    handled by the vizualization module.
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
    This function is here temporarily and should be seen as trial. Should be
    handled by the vizualization module.
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
    #calibration = read_calibration()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    temp_path = os.path.join(dir_path, 'temp_files')
    turn = 0
    hexagons = read_hexagons(
            filename='hexagons%d.geojson' % turn, path=test_path)
    t0 = time.time()
    #hexagons = read_hexagons(filename='hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
    hexagons = structures.determine_dikes(hexagons)
    hexagons = structures.determine_channel(hexagons)
    t1 = time.time()
    print("Read hexagons: " + str(t1 - t0))
    node_grid = read_node_grid()
    model = D3D.initialize_model()
    flow_grid = create_flow_grid(model)
    t2 = time.time()
    print("Load node and flow grids: " + str(t2 - t1))
    node_grid = index_node_grid(hexagons, node_grid)
    flow_grid = index_flow_grid(hexagons, flow_grid)
    t3 = time.time()
    print("Index node and face grid: " + str(t3 - t2))
    node_grid = interpolate_node_grid(hexagons, node_grid)
    hexagons, flow_grid = roughness.hex_to_points(model, hexagons, flow_grid)
    with open(os.path.join(temp_path, 'node_grid_before%d.geojson' % turn), 'w') as f:
        geojson.dump(node_grid, f, sort_keys=True, indent=2)
    with open(os.path.join(temp_path, 'face_grid_vegetation.geojson'), 'w') as f:
        geojson.dump(flow_grid, f, sort_keys=True, indent=2)
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
        with open(os.path.join(temp_path, 'node_grid_after%d.geojson' % turn), 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open(os.path.join(temp_path, 'filled_node_grid%d.geojson' % turn), 'w') as f:
            geojson.dump(filled_node_grid, f, sort_keys=True,
                         indent=2)
    t8 = time.time()
    if save:
        print("Saved both grids: " + str(t8 - t7))
    heightmap = create_geotiff(node_grid)
    heatmap = create_roughness_map(flow_grid)
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
        with open(os.path.join(temp_path, 'hexagons_visualization_test.geojson'), 'w') as f:
            geojson.dump(hexagons, f, sort_keys=True,
                         indent=2)
        with open(os.path.join(temp_path, 'node_grid_visualization_test.geojson'), 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open(os.path.join(temp_path, 'face_grid_visualization_test.geojson'), 'w') as f:
            geojson.dump(flow_grid, f, sort_keys=True,
                         indent=2)
        print("saved files")
