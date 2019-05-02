# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 16:49:15 2019

@author: haanrj
"""

import json
import time
import cv2
import geojson
import numpy as np
import gridCalibration as cali
import sandbox_fm.calibrate
from shapely.geometry import asShape


def detect_markers(file, pers, img_x, img_y, origins, r, features,
                   method='rgb'):
    # load and process the new image (game state)
    img = cv2.imread(file)
    # warp image it to calibrated perspective
    warped = cv2.warpPerspective(img, pers, (img_x, img_y))
    if method is 'LAB':
        lab = cv2.cvtColor(warped, cv2.COLOR_BGR2Lab)
        L, A, B = cv2.split(lab)
        A = cv2.medianBlur(A, 5)
        B = cv2.medianBlur(B, 5)
        # set ranges for blue and red to create masks, may need updating
        lower_blue = 0
        upper_blue = 110
        lower_red = 160
        upper_red = 255
        # isolate red and blue in the image
        blue_mask = cv2.inRange(B, lower_blue, upper_blue)
        red_mask = cv2.inRange(A, lower_red, upper_red)
        # add dilation to the image
        kernel = np.ones((2,2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations = 1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations = 1)
        cv2.imwrite('red_mask_dilated_LAB.jpg', red_dilate)
        cv2.imwrite('blue_mask_dilated_LAB.jpg', blue_dilate)
    elif method is 'YCrCb':
        ycrcb = cv2.cvtColor(warped, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycrcb)
        Cb = cv2.medianBlur(Cb, 5)
        Cr = cv2.medianBlur(Cr, 5)
        # set ranges for blue and red to create masks, may need updating
        lower_blue = 160
        upper_blue = 255
        lower_red = 160
        upper_red = 255
        # isolate red and blue in the image
        blue_mask = cv2.inRange(Cb, lower_blue, upper_blue)
        red_mask = cv2.inRange(Cr, lower_red, upper_red)
        # add dilation to the image
        kernel = np.ones((2,2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations = 1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations = 1)
        cv2.imwrite('red_mask_dilated_YCrCb.jpg', red_dilate)
        cv2.imwrite('blue_mask_dilated_YCrCb.jpg', blue_dilate)
    else:
        B, G, R = cv2.split(warped)
        B = cv2.medianBlur(B, 5)
        R = cv2.medianBlur(R, 5)
        # set ranges for blue and red to create masks, may need updating
        lower_blue = 220
        upper_blue = 255
        lower_red = 230
        upper_red = 255
        # isolate red and blue in the image
        blue_mask = cv2.inRange(B, lower_blue, upper_blue)
        red_mask = cv2.inRange(R, lower_red, upper_red)
        # add dilation to the image
        kernel = np.ones((2,2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations = 1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations = 1)
        # save masks, can be removed later
        cv2.imwrite('red_mask_dilated_RGB.jpg', red_dilate)
        cv2.imwrite('blue_mask_dilated_RGB.jpg', blue_dilate)
   
    # create a mask for the region of interest processing
    y_cell = int(round(r / 2)) # convert diameter to actual radius as int value
    x_cell = int(round(1.25 * y_cell))
    margin = int(round(y_cell * 0.95)) # slightly lower radius to create a mask that removes contours from slight grid misplacement
    mask = np.zeros((2 * y_cell, 2 * x_cell), dtype="uint8") # empty mask of grid cell size
    dist = margin/np.cos(np.deg2rad(30))
    x_jump = int(round(dist/2))
    y_jump = margin
    dist = int(round(dist))
    point1 = [x_cell+dist, y_cell]
    point2 = [x_cell+x_jump, y_cell+y_jump]
    point3 = [x_cell-x_jump, y_cell+y_jump]
    point4 = [x_cell-dist, y_cell]
    point5 = [x_cell-x_jump, y_cell-y_jump]
    point6 = [x_cell+x_jump, y_cell-y_jump]
    pts = np.array([point1, point2, point3, point4, point5, point6], np.int32)
    cv2.fillPoly(mask, [pts], (255,255,255))
    # for loop that analyzes all grid cells
    for i, feature in enumerate(features):
        #geometry = asShape(feature.geometry)
        x = feature.properties["x_center"]
        y = feature.properties["y_center"]
        if i < 10:
            x = x - 7
        elif i < 19:
            x = x - 5
        elif i < 29:
            x = x - 3
        elif i < 38:
            x = x - 2
        elif i < 48:
            x = x - 1
        elif i < 95:
            pass
        elif i < 105:
            x = x + 1
        elif i < 114:
            x = x + 2
        elif i < 124:
            x = x + 3
        elif i < 133:
            x = x + 5
        else:
            x = x + 7
        """
        point1 = [x+dist, y]
        point2 = [x+x_jump, y+y_jump]
        point3 = [x-x_jump, y+y_jump]
        point4 = [x-dist, y]
        point5 = [x-x_jump, y-y_jump]
        point6 = [x+x_jump, y-y_jump]
        pts = np.array([point1, point2, point3, point4,
                        point5, point6], np.int32)
        cv2.polylines(warped, [pts], True, (255,255,255))
        """
        
        # get region of interest (ROI) for red (geometry) and analyse number
        # of contours (which identifies the markers) found
        roiGeo = red_dilate[y-y_cell:y+y_cell, x-x_cell:x+x_cell]
        # mask the ROI to eliminate adjacent grid cells
        maskedImgGeo = cv2.bitwise_and(roiGeo, roiGeo, mask = mask)
        # find contours within masked ROI
        im1, contoursGeo, hierarchy1 = cv2.findContours(maskedImgGeo,
                                                        cv2.RETR_CCOMP,
                                                        cv2.CHAIN_APPROX_SIMPLE)

        # same as above for blue (ecotopes) as above
        roiEco = blue_dilate[y-y_cell:y+y_cell, x-x_cell:x+x_cell]
        maskedImgEco = cv2.bitwise_and(roiEco, roiEco, mask=mask)
        im2, contoursEco, hierarchy2 = cv2.findContours(maskedImgEco,
                                                        cv2.RETR_CCOMP,
                                                        cv2.CHAIN_APPROX_SIMPLE)
        """
        # store each analyzed ROI, not necessary for the script to work
        filenameGeo = 'geo_roi_%i.jpg'%i
        filenameEco = 'eco_roi_%i.jpg'%i
        cv2.imwrite(filenameGeo, maskedImgGeo)
        cv2.imwrite(filenameEco, maskedImgEco)
        """
        feature.properties["tygron_id"] = i
        feature.properties["z"] = len(contoursGeo)
        feature.properties["landuse"] = len(contoursEco)
    #cv2.imwrite('cells.jpg', warped)
    hexagons = geojson.FeatureCollection(features)
    with open('hexagons.geojson', 'w') as f:
        geojson.dump(hexagons, f, sort_keys=True,
                     indent=2)
    return hexagons


def transform(features, transforms, export=None):
    """
    Function that transforms geojson files to new coordinates based on where
    the geojson needs to be transformed to (e.g. from the image processed to
    the model: 'img_post_cut2model').
    """
    transformed_features = []
    waterbodies = []
    landbodies = []
    if export == "sandbox":
        transform = transforms['img_post_cut2model']
    elif export == "tygron_initialize":
        transform = transforms['img_post_cut2tygron_export']
    elif export == "tygron":
        transform = transforms['img_post_cut2tygron_update']
    else:
        print("unknown export method, current supported are: 'sandbox', "
              "'tygron' & 'tygron_initialize'")
        return features
    for feature in features.features:
        pts = np.array(feature.geometry["coordinates"][0], dtype="float32")
        # points should be channels
        # pts = np.c_[pts, np.zeros_like(pts[:, 0])]
        x, y = pts[:, 0], pts[:, 1]
        x_t, y_t = sandbox_fm.calibrate.transform(x, y, transform)
        xy_t = np.c_[x_t, y_t]
        new_feature = geojson.Feature(id=feature.id,
                                      geometry=geojson.Polygon([xy_t.tolist()]),
                                      properties=feature.properties)
        if export == "tygron":
            if feature.properties["z"] < 2:
                waterbodies.append(new_feature)
            else:
                landbodies.append(new_feature)
        transformed_features.append(new_feature)
    if export == "sandbox":
        transformed_features = geojson.FeatureCollection(transformed_features)
        with open('hexagons_sandbox_transformed.geojson', 'w') as f:
            geojson.dump(transformed_features, f, sort_keys=True, indent=2)
        return transformed_features
    elif export == "tygron_initialize":
        crs = {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::3857"
                }
            }
        transformed_features = geojson.FeatureCollection(transformed_features,
                                                         crs=crs)
        with open('hexagons_tygron_transformed.geojson', 'w') as f:
            geojson.dump(transformed_features, f, sort_keys=True, indent=2)
        return transformed_features
    else:
        transformed_features = geojson.FeatureCollection(transformed_features)
        with open('hexagons_tygron_update_transformed.geojson', 'w') as f:
            geojson.dump(transformed_features, f, sort_keys=True, indent=2)
        waterbodies = geojson.FeatureCollection(waterbodies)
        with open('waterbodies_tygron_transformed.geojson', 'w') as f:
            geojson.dump(waterbodies, f, sort_keys=True, indent=2)
        landbodies = geojson.FeatureCollection(landbodies)
        with open('landbodies_tygron_transformed.geojson', 'w') as f:
            geojson.dump(landbodies, f, sort_keys=True, indent=2)
        return waterbodies, landbodies


if __name__ == '__main__':
    tic = time.time()  # start performance timer
    filename = 'board_image0.jpg'
    #filename = 'webcam_test.jpg'
    # image name for calibration (would be first image pre-session)
    canvas, thresh = cali.detect_corners(filename, method='adaptive')
    # store calibration values as global variables
    pers, img_x, img_y, origins, radius, cut_points, \
        features = cali.rotate_grid(canvas, thresh)
    transforms = cali.create_calibration_file(img_x, img_y, cut_points)

    with open('hexagons_features.json', 'w') as g:
        json.dump(features, g, sort_keys=True, indent=2)
    tac = time.time()  # calibration performance timer
    # initiate the image processing function
    hexagon_current = detect_markers(filename, pers, img_x, img_y, origins,
                                     radius, features, transforms)
    toc = time.time()  # end performance timer
    # print calibration and image processing performance time
    print('calibration time:', tac-tic)
    print('image processing time:', toc-tac)
