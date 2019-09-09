# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 10:49:34 2019

@author: haanrj
"""


import json
import os
import cv2
import numpy as np
import geojson
#import sandbox_fm.calibrate
#from sandbox_fm.calibration_wizard import NumpyEncoder


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)


def create_calibration_file(img_x=None, img_y=None, cut_points=None, path="",
                            test=False, save=False):
    """
    Function that creates the calibration file (json format) and returns the
    transforms that can be used by other functions.
    """
    def compute_transforms(calibration):
        """compute transformation matrices based on calibration data"""
    
        point_names = [
            "model",
            "img",
            "box",
            "img_pre_cut",
            "img_post_cut",
            "beamer",
    		"tygron_export",
    		"tygron_update"
        ]
        """
        WIDTH, HEIGHT = 640, 480
        
        DEFAULT_BOX = np.array([
            [0, 0],
            [WIDTH, 0],
            [WIDTH, HEIGHT],
            [0, HEIGHT]
        ], dtype='float32')
        """
        
        point_arrays = {}
        for name in point_names:
            """
            if name == 'box':
                arr = np.array(DEFAULT_BOX, dtype='float32')
            el
            """
            if name in calibration:
                arr = np.array(calibration[name], dtype='float32')
            elif name + "_points" in calibration:
                arr = np.array(calibration[name + "_points"], dtype='float32')
            else:
                continue
            point_arrays[name] = arr
    
        transforms = {}
        for a in point_names:
            for b in point_names:
                if a == b:
                    continue
                if not (a in point_arrays):
                    continue
                if not (b in point_arrays):
                    continue
                transform_name = a + '2' + b
                transform = cv2.getPerspectiveTransform(
                    point_arrays[a],
                    point_arrays[b]
                )
                transforms[transform_name] = transform
    
        return transforms
    
    calibration = {}
    # model points following SandBox implementation; 
    # between [-600, -400] and [600, 400] 
    calibration['model_points'] = (
            [-400, 300 ], [400, 300], [400, -300], [-400, -300])
    # resolution camera; FullHD
    calibration['img_points'] = [0, 0], [1920, 0], [1920, 1080], [0, 1080]
    if not test:
        # calibration points used to cut images
        calibration['img_pre_cut_points'] = cut_points.tolist()
        # corners of image after image cut
        calibration['img_post_cut_points'] = (
                [0, 0], [img_x, 0], [img_x, img_y],  [0, img_y])
    # tygron project creation; empty world coordinates
    calibration['tygron_export'] = [0, 0], [1000, 0], [1000, -750],  [0, -750]
    # tygron project update; world coordinates once created
    calibration['tygron_update'] = [0, 0], [1000, 0], [1000, -750],  [0, -750]
    # height range
    calibration['z'] = [0.0, 21.2]
    # height of game pieces; may be subject to change after interpolation
    calibration['z_values'] = [0, 5]
    # box == beamer
    calibration['box'] = [0, 0], [640, 0], [640, 480], [0, 480]
    #transforms = sandbox_fm.calibrate.compute_transforms(calibration)
    transforms = compute_transforms(calibration)
    calibration.update(transforms)
    if save:
        with open(os.path.join(path, 'calibration.json'), 'w') as f:
            json.dump(calibration, f, sort_keys=True, indent=2,
                      cls=NumpyEncoder)
    return transforms


def detect_corners(img, method='standard', path=""):
    # TO DO: get path from main program
    """
    Function that detects the corners of the board (the four white circles)
    and returns their coordinates as a 2D array.
    """
    height, width, channels = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # convert image to grayscale
    if method == 'adaptive':
        blur = cv2.medianBlur(gray, 5)  # blur grayscale image
        thresh = cv2.adaptiveThreshold(blur, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        # store threshold image
        cv2.imwrite(os.path.join(path, 'Adaptive_threshold.jpg'), thresh)
    else:
        blur = cv2.GaussianBlur(gray, (5, 5), 0)  # blur grayscale image
        # threshold grayscale image as binary
        ret, thresh = cv2.threshold(blur, 0, 255,
                                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # store threshold image
        cv2.imwrite(os.path.join(path, 'Standard_threshold.jpg'), thresh)

    # create mask to only search for circles in the corner since we know that's
    # where the circles are. The code is rather sensitive and sometimes it sees
    # incorrect circles. This section prevents that from happening. Even when
    # it does however, it still detects the real circles more clearly, thus
    # lists them in index 0-3.
    mask = np.zeros((height, width), dtype="uint8") 
    margin_x = round(width * 0.2)
    margin_y = round(height * 0.14)
    cv2.rectangle(mask, (0, 0), (margin_x, margin_y), (255, 255, 255), -1)
    cv2.rectangle(mask, (width-margin_x, 0), (width, margin_y),
                  (255, 255, 255), -1)
    cv2.rectangle(mask, (0, height-margin_y), (margin_x, height),
                  (255, 255, 255), -1)
    cv2.rectangle(mask, (width-margin_x, height-margin_y), (width, height),
                  (255, 255, 255), -1)
    masked_tresh = cv2.bitwise_and(thresh, thresh, mask=mask)

    # detect corner circles in the image (min/max radius ensures only
    # finding those we want)
    circles = cv2.HoughCircles(masked_tresh, cv2.HOUGH_GRADIENT, 1, 200,
                               param1=50, param2=14, minRadius=18,
                               maxRadius=21)

    # ensure at least some circles were found, such falesafes (also for certain
    # error types) should be build in in later versions --> this should have
    # the effect that the script either aborts or goes to test mode.
    if circles is None:
        print('ERROR: No circles were detected in the image')
        return
    # convert the (x, y) coordinates and radius of the circles to integers
    circles = np.round(circles[0, :]).astype("int")
    # loop over the (x, y) coordinates and radius of the circles
    canvas = circles[:, :2]

    # this drawing of the circles is not necessary for the program to run. Left
    # in as it only happens in the initialization.
    for (x, y, r) in circles:
        # draw circle around detected corner
        cv2.circle(img, (x, y), r, (0, 255, 0), 4)
        # draw rectangle at center of detected corner
        cv2.rectangle(img, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
    # store the corner detection image
    cv2.imwrite(os.path.join(path, 'CornersDetected.jpg'), img)
    return canvas, thresh


def rotate_grid(canvas, img):
    """
    Function that sorts the four corners in the right order (top left, top
    right, bottom right, bottom left) and returns the perspective transform
    to be used throughout the session.
    """
    # get index of one of the two top corners, store it and delete from array
    lowest_y = int(np.argmin(canvas, axis=0)[1:])
    top_corner1 = canvas[lowest_y]
    x1 = top_corner1[0]
    canvas = np.delete(canvas, (lowest_y), axis=0)

    # get index of the second top corner, store it and delete from array
    lowest_y = int(np.argmin(canvas, axis=0)[1:])
    top_corner2 = canvas[lowest_y]
    x2 = top_corner2[0]
    canvas = np.delete(canvas, (lowest_y), axis=0)

    # store the two bottom corners
    bottom_corner1 = canvas[0]
    x3 = bottom_corner1[0]
    bottom_corner2 = canvas[1]
    x4 = bottom_corner2[0]

    # sort corners along top left, top right, bottom left, bottom right
    if x1 > x2:
        top_left = top_corner2
        top_right = top_corner1
    else:
        top_left = top_corner1
        top_right = top_corner2
    if x3 > x4:
        bottom_left = bottom_corner2
        bottom_right = bottom_corner1
    else:
        bottom_left = bottom_corner1
        bottom_right = bottom_corner2

    # match image points to new corner points according to known ratio
    pts1 = np.float32([top_left, top_right, bottom_right, bottom_left])

    # this value needs changing according to image size
    img_y = 1000  # warped image height
    # height/width ratio given current grid
    ratio = 1.3861874976470018770202169598726
    img_x = int(round(img_y * ratio))  # warped image width
    # size for warped image
    pts2 = np.float32([[0, 0],[img_x, 0],[img_x, img_y],[0, img_y]])
    # get perspective to warp image
    perspective = cv2.getPerspectiveTransform(pts1, pts2)

    # warp image according to the perspective transform and store image
    # warped = cv2.warpPerspective(img, perspective, (img_x, img_y))
    # cv2.imwrite('warpedGrid.jpg', warped)
    #features, origins, radius = create_features(img_y, img_x)
    return perspective, img_x, img_y, pts1


def create_features(height, width):
    """
    Function that calculates the midpoint coordinates of each hexagon in the
    transformed picture.
    """
    # determine size of grid circles from image and step size in x direction
    radius = (height / 10)
    x_step = np.cos(np.deg2rad(30)) * radius
    origins = []
    column = []
    # determine x and y coordinates of gridcells midpoints
    for a in range(1, 16):  # range reflects gridsize in x direction
        x = (x_step * a)
        for b in range(1, 11):  # range reflects gridsize in y direction
            if a % 2 == 0:
                if b == 10:
                    continue
                y = (radius * b)
            else:
                y = (radius * (b - 0.5))
            origins.append([x, y])
            column.append(a)
    origins = np.array(origins)
    board_cells = len(origins)
    """
    code to add ghost cells.
    """
    y_jump = radius/2
    dist = y_jump/np.cos(np.deg2rad(30))
    x_jump = dist/2
    features = []
    for i, (x, y) in enumerate(origins):
        # determine all the corner points of the hexagon
        point1 = [x+dist, y]
        point2 = [x+x_jump, y+y_jump]
        point3 = [x-x_jump, y+y_jump]
        point4 = [x-dist, y]
        point5 = [x-x_jump, y-y_jump]
        point6 = [x+x_jump, y-y_jump]
        # create a geojson polygon for the hexagon
        polygon = geojson.Polygon([[point1, point2, point3, point4, point5,
                                    point6, point1]])
        feature = geojson.Feature(id=i, geometry=polygon)
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
        feature.properties["column"] = column[i]
        feature.properties["tygron_id"] = i
        # these x and y centers are not actually relevant --> features are
        # transformed to other coordinates.
        feature.properties["x_center"] = int(round(x))
        feature.properties["y_center"] = int(round(y))
        feature.properties["ghost_hexagon"] = False
        features.append(feature)
    x_left = origins[0][0] - (x_step * 5)
    ghost_origins = []
    ghost_columns = []
    next_column = max(column)
    for a in range(1, 5):  # range reflects gridsize in x direction
        x = x_left + (x_step * a)
        next_column += 1
        for b in range(1, 11):  # range reflects gridsize in y direction
            if a % 2 == 0:
                if b == 10:
                    continue
                y = (radius * b)
            else:
                y = (radius * (b - 0.5))
            ghost_origins.append([x, y])
            ghost_columns.append(next_column)
    x_right = origins[-1][0] + x_step
    for a in range(0, 4):  # range reflects gridsize in x direction
        x = x_right + (x_step * a)
        next_column += 1
        for b in range(1, 11):  # range reflects gridsize in y direction
            if a % 2 == 0:
                if b == 10:
                    continue
                y = (radius * b)
            else:
                y = (radius * (b - 0.5))
            ghost_origins.append([x, y])
            ghost_columns.append(next_column)
    """
    for b in range(1,11):
        x = x_left
        y = (radius * (b - 0.5))
        ghost_origins.append([x, y])
        ghost_columns.append(next_column)
    x_left += x_step
    next_column += 1
    for b in range(1,10):
        x = x_left
        y = radius * b
        ghost_origins.append([x, y])
        ghost_columns.append(next_column)
    next_column += 1
    for b in range(1,10):
        x = x_right
        y = radius * b
        ghost_origins.append([x, y])
        ghost_columns.append(next_column)
    x_right += x_step
    next_column += 1
    for b in range(1,11):
        x = x_right
        y = (radius * (b - 0.5))
        ghost_origins.append([x, y])
        ghost_columns.append(next_column)
    #vert_middle = width / 2
    #min_column = min(column)
    """
    for i, (x, y) in enumerate(ghost_origins):
        # determine all the corner points of the hexagon
        point1 = [x+dist, y]
        point2 = [x+x_jump, y+y_jump]
        point3 = [x-x_jump, y+y_jump]
        point4 = [x-dist, y]
        point5 = [x-x_jump, y-y_jump]
        point6 = [x+x_jump, y-y_jump]
        # create a geojson polygon for the hexagon
        polygon = geojson.Polygon([[point1, point2, point3, point4, point5,
                                    point6, point1]])
        ghost_id = i + board_cells
        feature = geojson.Feature(id=ghost_id, geometry=polygon)
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
        feature.properties["column"] = ghost_columns[i]
        feature.properties["tygron_id"] = None
        # these x and y centers are not actually relevant --> features are
        # transformed to other coordinates.
        feature.properties["x_center"] = int(round(x))
        feature.properties["y_center"] = int(round(y))
        feature.properties["ghost_hexagon"] = True
        
        features.append(feature)
    # create geojson featurecollection with all hexagons.
    features = geojson.FeatureCollection(features)
    with open('ghost_cells_test.geojson', 'w') as f:
        geojson.dump(features, f, sort_keys=True, indent=2)
    return features, origins, radius


def drawMask(origins, img, path=""):
    """
    Function that can be called to draw the mask and print hexagon numbers.
    This function is currently not called. Can be removed at a later stage.
    """
    global count
    global radius
    r = int(round(radius / 2))
    for (x, y, count) in origins:
        # draw the circle in the output image, then draw a rectangle
        # corresponding to the center of the circle
        cv2.circle(img, (x, y), r, (0, 255, 0), 4)
        #cv2.rectangle(img, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
        cv2.putText(img, str(count), (x - 50, y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 1)
    # save image with grid
    cv2.imwrite(os.path.join(path, 'drawGrid.jpg'), img)
    print('success')
    return
