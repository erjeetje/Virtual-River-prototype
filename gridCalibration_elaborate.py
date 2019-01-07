# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 10:49:34 2019

@author: haanrj
"""

import cv2
import numpy as np
import os

def detectCorners(filename):
    # find and create new paths for storing process images if these do not exists
    dir_path = dir_path = os.path.dirname(os.path.realpath(__file__))
    pic_path = os.path.join(dir_path, 'processing_files')
    try:
        # Create target Directory
        os.mkdir(pic_path)
        print("Directory " , pic_path ,  " Created ") 
    except FileExistsError:
        print("Directory " , pic_path ,  " already exists, files stored anyway")
    
    canvas = []
    img = cv2.imread(filename) # load image
    cv2.imwrite(os.path.join(pic_path, '00_Original_image_for_calibration.jpg'), img) # store grayscale image
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # convert image to grayscale
    cv2.imwrite(os.path.join(pic_path, '01_Calibration_image_grayscale.jpg'), gray) # store grayscale image
    blur = cv2.GaussianBlur(gray,(5,5),0) # flur grayscale image
    ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU) # threshold grayscale image as binary
    cv2.imwrite(os.path.join(pic_path, '02_Calibration_image_threshold.jpg'), thresh) # store threshold image
    
    # detect corner circles in the image (min/max radius ensures only finding those)
    circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT, 1, 200, param1 = 50, param2 = 15, minRadius = 50, maxRadius = 70)
    
    # ensure at least some circles were found, such falesafes (also for certain error types) should be build in in later versions
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")
        # loop over the (x, y) coordinates and radius of the circles
        for (x, y, r) in circles:
            cv2.circle(img, (x, y), r, (0, 255, 0), 4) # draw circle around detected corner
            cv2.rectangle(img, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1) # draw rectangle at center of detected corner
            canvas.append([x, y]) # store corner coordinates
        cv2.imwrite(os.path.join(pic_path, '03_CornersDetected.jpg'), img) # store the corner detection image
        """
        # storing corners for the perspective warp, disabled
        
        with open('circles_real.txt', 'w') as f:
            for item in circles:
                f.write("%s\n" % item)
        print('stored')
        """
        return np.array(canvas), thresh, pic_path
    else:
        print('no circles')
   
def rotateGrid(canvas, img, pic_path):
    # get index of one of the two highest corners, store it and delete from array
    lowest_y = int(np.argmin(canvas, axis=0)[1:])
    top_corner1 = canvas[lowest_y:lowest_y+1][0]
    x1 = top_corner1[0]
    canvas = np.delete(canvas, (lowest_y), axis=0)
    
    # get index of the second top corner, store it and delete from array
    lowest_y = int(np.argmin(canvas, axis=0)[1:])
    top_corner2 = canvas[lowest_y:lowest_y+1][0]
    x2 = top_corner2[0]
    canvas = np.delete(canvas, (lowest_y), axis=0)
    
    # store the two bottom corners
    bottom_corner1 = canvas[0:1][0]
    x3 = bottom_corner1[0]
    bottom_corner2 = canvas[1:2][0]
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
    pts1 = np.float32([top_left,top_right,bottom_left,bottom_right])
    
    # this value needs changing according to image size
    img_y = 3000 # warped image height
    ratio = 1.3861874976470018770202169598726 # height/width ratio given current grid
    img_x = int(round(img_y * ratio)) # warped image width
    pts2 = np.float32([[0,0],[img_x,0],[0,img_y],[img_x,img_y]])
    perspective = cv2.getPerspectiveTransform(pts1,pts2)
    
    # warp image according to the perspective transform and store image
    warped = cv2.warpPerspective(img,perspective,(img_x,img_y))
    cv2.imwrite(os.path.join(pic_path, '04_warpedGrid.jpg'), warped)
    origins, radius = calcGrid(img_y, img_x, pic_path)
    return perspective, img_x, img_y, origins, radius
    
def calcGrid(height, width, pic_path):
    # determine size of grid circles from image and step size in x direction
    radius = int(round(height / 10))
    x_step = np.cos(np.deg2rad(30)) * radius
    x_list = []
    y_list = []
    circ_origin = []
    
    # determine x and y coordinates of gridcells midpoints
    for a in range (1, 16):
        x = int(round(x_step * a))
        for b in range (1,11):
            if a % 2 == 0:
                if b == 10:
                    continue
                y = int(round(radius * b))
            else:
                y = int(round(radius * (b - 0.5)))
            x_list.append(x)
            y_list.append(y)
    
    # create array of x, y coordinates gridcells and gridcell number 
    for x, y in zip(x_list, y_list):
        circ_origin.append([x, y])
    origins = np.array(circ_origin)
    
    # backup x, y coordinates and gridcell numbers in a text file, unnecessary for script to work
    with open(os.path.join(pic_path, '05_grid_coordinates.txt'), 'w') as f:
        for item in origins:
            f.write("%s\n" % item)       
    return origins, radius

"""
# this function draws the grid as calculated by calcGrid function. Not called in the script

def drawMask(origins, img):
    global count
    global radius
    r = int(round(radius / 2))
    for (x, y, count) in origins:
        # draw the circle in the output image, then draw a rectangle
        # corresponding to the center of the circle
        cv2.circle(img, (x, y), r, (0, 255, 0), 4)
        #cv2.rectangle(img, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
        cv2.putText(img, str(count), (x - 50, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 1)   
    # save image with grid
    cv2.imwrite('drawGrid.jpg', img)
    print('success')
    return  
"""