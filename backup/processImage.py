# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 16:49:15 2019

@author: haanrj
"""

import json
import os
import time
import cv2
import geojson
import numpy as np
import gridCalibration as cali
import sandbox_fm.calibrate


def detect_markers(img, pers, img_x, img_y, origins, r, features, turn=0,
                   method='rgb', path=""):
    # warp image it to calibrated perspective
    warped = cv2.warpPerspective(img, pers, (img_x, img_y))
    # save the file of this turn
    filename = 'turn_%d.jpg' % turn
    cv2.imwrite(os.path.join(path, filename), warped)
    if method is 'LAB':
        # convert the image to labspace and get the A and B channels.
        lab = cv2.cvtColor(warped, cv2.COLOR_BGR2Lab)
        L, A, B = cv2.split(lab)
        A = cv2.medianBlur(A, 5)
        B = cv2.medianBlur(B, 5)
        # set ranges for blue and red to create masks, may need updating.
        lower_blue = 0
        upper_blue = 110
        lower_red = 160
        upper_red = 255
        # isolate red and blue in the image.
        blue_mask = cv2.inRange(B, lower_blue, upper_blue)
        red_mask = cv2.inRange(A, lower_red, upper_red)
        # add dilation to the image.
        kernel = np.ones((2, 2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations=1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations=1)
        cv2.imwrite(os.path.join(path, 'red_mask_dilated_LAB%d.jpg' % turn),
                    red_dilate)
        cv2.imwrite(os.path.join(path, 'blue_mask_dilated_LAB%d.jpg' % turn),
                    blue_dilate)
    elif method is 'YCrCb':
        # convert to image to YCRCb and get the Cb and Cr channels.
        ycrcb = cv2.cvtColor(warped, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycrcb)
        Cb = cv2.medianBlur(Cb, 5)
        Cr = cv2.medianBlur(Cr, 5)
        # set ranges for blue and red to create masks, may need updating.
        lower_blue = 160
        upper_blue = 255
        lower_red = 160
        upper_red = 255
        # isolate red and blue in the image.
        blue_mask = cv2.inRange(Cb, lower_blue, upper_blue)
        red_mask = cv2.inRange(Cr, lower_red, upper_red)
        # add dilation to the image.
        kernel = np.ones((2, 2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations=1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations=1)
        cv2.imwrite(os.path.join(path, 'red_mask_dilated_YCrCb%d.jpg' % turn),
                    red_dilate)
        cv2.imwrite(os.path.join(path, 'blue_mask_dilated_YCrCb%d.jpg' % turn),
                                 blue_dilate)
    else:
        # split the RGB channels and get the B and R channels.
        B, G, R = cv2.split(warped)
        B = cv2.medianBlur(B, 5)
        R = cv2.medianBlur(R, 5)
        # set ranges for blue and red to create masks, may need updating.
        lower_blue = 220
        upper_blue = 255
        lower_red = 230
        upper_red = 255
        # isolate red and blue in the image.
        blue_mask = cv2.inRange(B, lower_blue, upper_blue)
        red_mask = cv2.inRange(R, lower_red, upper_red)
        # add dilation to the image.
        kernel = np.ones((2, 2), np.uint8)
        red_dilate = cv2.dilate(red_mask, kernel, iterations=1)
        blue_dilate = cv2.dilate(blue_mask, kernel, iterations=1)
        # save masks, can be removed later.
        cv2.imwrite(os.path.join(path, 'red_mask_dilated_RGB%d.jpg' % turn),
                    red_dilate)
        cv2.imwrite(os.path.join(path, 'blue_mask_dilated_RGB%d.jpg' % turn),
                    blue_dilate)

    # create a mask for the region of interest processing.
    # convert diameter to actual radius as int value.
    y_cell = int(round(r / 2))
    x_cell = int(round(1.25 * y_cell))
    # slightly lower radius to create a mask that removes contours from slight
    # grid misplacement.
    margin = int(round(y_cell * 0.92))
    # empty mask of grid cell size.
    mask = np.zeros((2 * y_cell, 2 * x_cell), dtype="uint8")
    # calculate the x and y differences for the points of the hexagon shaped
    # mask.
    dist = margin/np.cos(np.deg2rad(30))
    x_jump = int(round(dist/2))
    y_jump = margin
    dist = int(round(dist))
    # define the 6 corner points of the hexagon shaped mask.
    point1 = [x_cell+dist, y_cell]
    point2 = [x_cell+x_jump, y_cell+y_jump]
    point3 = [x_cell-x_jump, y_cell+y_jump]
    point4 = [x_cell-dist, y_cell]
    point5 = [x_cell-x_jump, y_cell-y_jump]
    point6 = [x_cell+x_jump, y_cell-y_jump]
    # create the mask.
    pts = np.array([point1, point2, point3, point4, point5, point6], np.int32)
    cv2.fillPoly(mask, [pts], (255, 255, 255))

    if False:
        # create folders to store individual cells if wanted. Currently set in
        # a if False statement and skipped.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(dir_path, 'image_processing_files')
        try:
            os.mkdir(dir_path)
            print("Directory ", dir_path, " created.")
        except FileExistsError:
            print("Directory ", dir_path,
                  " already exists, overwriting files.")
        geo_path = os.path.join(dir_path, 'geometry_rois')
        try:
            os.mkdir(geo_path)
            print("Directory ", geo_path, " created.")
        except FileExistsError:
            print("Directory ", geo_path,
                  " already exists, overwriting files.")
        landuse_path = os.path.join(dir_path, 'land_use_rois')
        try:
            os.mkdir(landuse_path)
            print("Directory ", landuse_path, " created.")
        except FileExistsError:
            print("Directory ", landuse_path,
                  " already exists, overwriting files.")
    
    # for loop that analyzes all grid cells.
    for i, feature in enumerate(features.features):
        # some adjustments to adjust for the distance of the camera to the
        # side. This is not a necessity, but increases robustness. Alternative
        # would be to improve the perspective warp.
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
        # get region of interest (ROI) for red (geometry) and analyse number
        # of contours (which identifies the markers) found.
        roiGeo = red_dilate[y-y_cell:y+y_cell, x-x_cell:x+x_cell]
        # mask the ROI to eliminate adjacent grid cells.
        maskedImgGeo = cv2.bitwise_and(roiGeo, roiGeo, mask=mask)
        # find contours within masked ROI.
        im1, contoursGeo, h1 = cv2.findContours(maskedImgGeo, cv2.RETR_CCOMP,
                                                cv2.CHAIN_APPROX_SIMPLE)
        # same as above for blue (land use) as above.
        roiEco = blue_dilate[y-y_cell:y+y_cell, x-x_cell:x+x_cell]
        maskedImgEco = cv2.bitwise_and(roiEco, roiEco, mask=mask)
        im2, contoursEco, h2 = cv2.findContours(maskedImgEco, cv2.RETR_CCOMP,
                                                cv2.CHAIN_APPROX_SIMPLE)
        # store each analyzed ROI, not necessary for the script to work.
        # currently set in an if False statement, thus skipped.
        if False:
            filenameGeo = 'geo_roi_%i.jpg'%i
            filenameEco = 'eco_roi_%i.jpg'%i
            cv2.imwrite(filenameGeo, maskedImgGeo)
            cv2.imwrite(filenameEco, maskedImgEco)
        
        # z range between 0 and 5, with 4 as a dike and 5 a reinforced dike
        # this should eventually be changed to match the model's height scale
        # directly.
        # z values should be adjusted to sandbox. Possibly test with new range.
        feature.properties["z"] = min(len(contoursGeo), 5)
        feature.properties["landuse"] = min(len(contoursEco), 9)
        if (feature.properties["landuse"] == 0 and
            feature.properties["z"] >= 4):
            feature.properties["landuse"] = 10
        if feature.properties["z"] < 2:
            feature.properties["water"] = True
            feature.properties["land"] = False
        else:
            feature.properties["water"] = False
            feature.properties["land"] = True
    return features


def transform(features, transforms, export=None, path=""):
    """
    Function that transforms geojson files to new coordinates based on where
    the geojson needs to be transformed to (e.g. from the image processed to
    the model: 'img_post_cut2model').
    """
    transformed_features = []
    # get correct transform.
    if export == "sandbox":
        transform = transforms['img_post_cut2model']
    elif export == "tygron_initialize":
        transform = transforms['img_post_cut2tygron_export']
    elif export == "tygron":
        transform = transforms['img_post_cut2tygron_update']
    elif export == "sandbox2tygron":
        transform = transforms['model2tygron_update']
    else:
        print("unknown export method, current supported are: 'sandbox', "
              "'tygron' & 'tygron_initialize'")
        return features
    # transform each feature to new coordinates.
    for feature in features.features:
        pts = np.array(feature.geometry["coordinates"][0], dtype="float32")
        # points should be channels.
        x, y = pts[:, 0], pts[:, 1]
        x_t, y_t = sandbox_fm.calibrate.transform(x, y, transform)
        xy_t = np.c_[x_t, y_t]
        new_feature = geojson.Feature(id=feature.id,
                                      geometry=geojson.Polygon([xy_t.tolist()]),
                                      properties=feature.properties)
        transformed_features.append(new_feature)
    # different export handlers.
    if export == "sandbox":
        transformed_features = geojson.FeatureCollection(transformed_features)
        if False:
            # saving transform is currently disables (hence if False). False
            # are stored centrally instead. remove after testing if
            # implementation functions correctly.
            with open(
                    os.path.join(path, 'hexagons_sandbox_transformed.geojson'),
                    'w') as f:
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
        if False:
            # saving transform is currently disables (hence if False). False
            # are stored centrally instead. remove after testing if
            # implementation functions correctly.
            with open(
                    os.path.join(path, 'hexagons_tygron_transformed.geojson'),
                    'w') as f:
                geojson.dump(transformed_features, f, sort_keys=True, indent=2)
        return transformed_features
    else:
        transformed_features = geojson.FeatureCollection(transformed_features)
        if False:
            # saving transform is currently disables (hence if False). False
            # are stored centrally instead. remove after testing if
            # implementation functions correctly.
            with open(
                    os.path.join(path,
                                 'hexagons_tygron_update_transformed.geojson'),
                    'w') as f:
                geojson.dump(transformed_features, f, sort_keys=True, indent=2)
        return transformed_features


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
