# -*- coding: utf-8 -*-
"""
Created on Thu Feb 28 16:07:11 2019

@author: HaanRJ
"""
import json
import cv2
import geojson
import numpy as np
#from scipy import interpolate
from scipy import spatial
#import rtree
from shapely import geometry
from shapely.ops import unary_union
import time
import netCDF4
import bmi.wrapper


def read_calibration():
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
    #with open('tygron_export.geojson', 'w') as f:
        #geojson.dump(board_featurecollection, f, sort_keys=True, indent=2)
    return calibration


def read_hexagons():
    with open('hexagons_sandbox_transformed.geojson') as f:
        features = geojson.load(f)
    return features


def read_grid():
    ds = netCDF4.Dataset(r'D:\Werkzaamheden map\Onderzoek\Design 2018\Models\300x200_2_net.nc')
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
    with open('grid.geojson', 'w') as f:
        geojson.dump(feature_collection, f, sort_keys=True, indent=2)
    return feature_collection


def hex_to_points(hexagons, grid, method='nearest'):
    hex_coor = []
    polygons = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        hex_coor.append([x_hex, y_hex])
        polygons.append(shape)
    hex_coor = np.array(hex_coor)
    hex_locations = spatial.cKDTree(hex_coor)
    multipolygon = geometry.MultiPolygon(polygons)
    board_as_polygon = unary_union(multipolygon)
    board_shapely = geometry.mapping(board_as_polygon)
    board_feature = geojson.Feature(geometry=board_shapely)
    board_featurecollection = geojson.FeatureCollection([board_feature])
    #print(board_shapely)
    with open('board_border.geojson', 'w') as f:
        geojson.dump(board_featurecollection, f, sort_keys=True, indent=2)
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
    bbox=geometry.Polygon([(minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny), (minx, maxy)])
    #print(bbox)
    inside_id = []
    inside_coor = []
    for feature in grid.features:
        point = geometry.asShape(feature.geometry)
        if bbox.contains(point):
            feature.properties["board"] = True
            inside_id.append(feature.id)
            x_point = point.centroid.x
            y_point = point.centroid.y
            inside_coor.append([x_point, y_point])
        else:
            feature.properties["board"] = False

    inside_coor = np.array(inside_coor)
    inside_locations = spatial.cKDTree(inside_coor)
    nearest = {}
    distances = {}
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}

    for feature in grid.features:
        shape = geometry.asShape(feature.geometry)
        x_hex = shape.centroid.x
        y_hex = shape.centroid.y
        xy = np.array([x_hex, y_hex])
        if feature.properties["board"]:
            dist, indices = hex_locations.query(xy, k=3)
            nearest[feature.id] = indices.tolist()
            distances[feature.id] = dist.tolist()
        else:
            dist, indices = inside_locations.query(xy)
            nearest[feature.id] = indices
            distances[feature.id] = dist
            """
            change this section to finding the nearest neighbour on the horizontal axis +
            another rule if no nearest neighbour on the horizontal axis
            """
    for feature in grid.features:
        if feature.properties["board"]:
            nearest_three = nearest[feature.id]
            distances2hex = distances[feature.id]
            if distances2hex[0] > 35:
                if distances2hex[1] <= 60:
                    if distances2hex[2] <= 60:
                        hexagon1 = hexagons_by_id[nearest_three[0]]
                        hexagon2 = hexagons_by_id[nearest_three[1]]
                        hexagon3 = hexagons_by_id[nearest_three[2]]
                        distances2hex = np.power(distances2hex, 2)
                        dist2hex1 = 1 / distances2hex[0]
                        dist2hex2 = 1 / distances2hex[1]
                        dist2hex3 = 1 / distances2hex[2]
                        total_dist = dist2hex1 + dist2hex2 + dist2hex3
                        feature.properties['z'] = round(hexagon1.properties['z'] * (dist2hex1 / total_dist) + hexagon2.properties['z'] * (dist2hex2 / total_dist) + hexagon3.properties['z'] * (dist2hex3 / total_dist), 5)
                    else:
                        hexagon1 = hexagons_by_id[nearest_three[0]]
                        hexagon2 = hexagons_by_id[nearest_three[1]]
                        distances2hex = np.power(distances2hex, 2)
                        dist2hex1 = 1 / distances2hex[0]
                        dist2hex2 = 1 / distances2hex[1]
                        total_dist = dist2hex1 + dist2hex2
                        feature.properties['z'] = round(hexagon1.properties['z'] * (dist2hex1 / total_dist) + hexagon2.properties['z'] * (dist2hex2 / total_dist), 5)
                else:
                    hexagon = hexagons_by_id[nearest_three[0]]
                    feature.properties['z'] = hexagon.properties['z']
                """
                hexagon1 = hexagons_by_id[nearest_three[0]]
                hexagon2 = hexagons_by_id[nearest_three[1]]
                hexagon3 = hexagons_by_id[nearest_three[2]]
                distances2hex = np.power(distances2hex, 2)
                dist2hex1 = 1 / distances2hex[0]
                dist2hex2 = 1 / distances2hex[1]
                dist2hex3 = 1 / distances2hex[2]
                total_dist = dist2hex1 + dist2hex2 + dist2hex3
                feature.properties['z'] = round(hexagon1.properties['z'] * (dist2hex1 / total_dist) + hexagon2.properties['z'] * (dist2hex2 / total_dist) + hexagon3.properties['z'] * (dist2hex3 / total_dist), 5)
                """
            elif distances2hex[1] > 45:
                hexagon = hexagons_by_id[nearest_three[0]]
                feature.properties['z'] = hexagon.properties['z']
            elif distances2hex[2] > 45:
                hexagon1 = hexagons_by_id[nearest_three[0]]
                hexagon2 = hexagons_by_id[nearest_three[1]]
                distances2hex = np.power(distances2hex, 2)
                dist2hex1 = 1 / distances2hex[0]
                dist2hex2 = 1 / distances2hex[1]
                total_dist = dist2hex1 + dist2hex2
                feature.properties['z'] = round(hexagon1.properties['z'] * (dist2hex1 / total_dist) + hexagon2.properties['z'] * (dist2hex2 / total_dist), 5)
            else:
                hexagon1 = hexagons_by_id[nearest_three[0]]
                hexagon2 = hexagons_by_id[nearest_three[1]]
                hexagon3 = hexagons_by_id[nearest_three[2]]
                distances2hex = np.power(distances2hex, 2)
                dist2hex1 = 1 / distances2hex[0]
                dist2hex2 = 1 / distances2hex[1]
                dist2hex3 = 1 / distances2hex[2]
                total_dist = dist2hex1 + dist2hex2 + dist2hex3
                feature.properties['z'] = round(hexagon1.properties['z'] * (dist2hex1 / total_dist) + hexagon2.properties['z'] * (dist2hex2 / total_dist) + hexagon3.properties['z'] * (dist2hex3 / total_dist), 5)
        else:
            continue

    grid_by_id = {feature.id: feature for feature in grid.features}
    for feature in grid.features:
        if not feature.properties["board"]:
            inside_point = grid_by_id[inside_id[nearest[feature.id]]]
            feature.properties['z'] = inside_point.properties['z']
        else:
            continue

    """
    Optie:
        - binnen bord True boolean
        - buiten bord False boolean
        - True --> nearest three hexagons (huidige implementatie)
        - False --> zoek nearest horizontale neighbour die True is
        - Geen nearest neighbour horizontaal --> nearest hexagon
    """

    with open('grid_with_z_triangulate2.geojson', 'w') as f:
        geojson.dump(grid, f, sort_keys=True, indent=2)
    return grid


def create_geotiff(grid):
    columns = []
    rows = []
    z= []
    for feature in grid.features:
        if feature.properties["board"]:
            shape = geometry.asShape(feature.geometry)
            x_point = shape.centroid.x
            y_point = shape.centroid.y
            if x_point not in columns:
                columns.append(x_point)
            if y_point not in rows:
                rows.append(y_point)
            z.append(feature.properties["z"])
        else:
            continue
    z = np.array(z)
    z = np.reshape(z, (len(rows),len(columns)))
    #z = np.flip(z, 0)
    #z = z.T
    with open('z_array_test.txt', 'w') as f:
        for item in z:
            f.write("%s\n" % item)
    print(columns)
    print(rows)
    #print(len(columns), len(rows))
    return


if __name__ == "__main__":
    tic = time.time()
    calibration = read_calibration()
    hexagons = read_hexagons()
    grid = read_grid()
    tac = time.time()
    grid_triangulate = hex_to_points(hexagons, grid, method='griddata')
    create_geotiff(grid_triangulate)
    model = bmi.wrapper.BMIWrapper('dflowfm')
    model.initialize(r'C:\Users\HaanRJ\Documents\GitHub\sandbox-fm\models\sandbox\Waal_schematic\waal_with_side.mdu')
    print('model initialized')
    toc = time.time()
    print('loading time:', tac-tic)
    print('interpolation time:', toc-tac)