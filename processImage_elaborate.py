# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 16:49:15 2019

@author: haanrj
"""

import cv2
import numpy as np
import gridCalibration_elaborate as cali
import time
import os

def detectMarkers(file, pers, img_x, img_y, origins, r):
    # find and create new paths for storing process images if these do not exists
    dir_path = dir_path = os.path.dirname(os.path.realpath(__file__))
    pic_path = os.path.join(dir_path, 'processing_files')
    geo_path = os.path.join(dir_path, 'geometry_files')
    eco_path = os.path.join(dir_path, 'ecotopes_files')
    
    # if necessary, create the directories for storing files
    try:
        # Create target Directory
        os.mkdir(pic_path)
        print("Directory " , pic_path ,  " Created ") 
    except FileExistsError:
        print("Directory " , pic_path ,  " already exists, files stored anyway")
    try:
        # Create target Directory
        os.mkdir(geo_path)
        print("Directory " , geo_path ,  " Created ") 
    except FileExistsError:
        print("Directory " , geo_path ,  " already exists, files stored anyway")
    try:
        # Create target Directory
        os.mkdir(eco_path)
        print("Directory " , eco_path ,  " Created ") 
    except FileExistsError:
        print("Directory " , eco_path ,  " already exists, files stored anyway")
    
    img = cv2.imread(file)
    warped = cv2.warpPerspective(img,pers,(img_x,img_y)) # warp image it to calibrated perspective
    blur = cv2.GaussianBlur(warped,(25,25),0) # blur image
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV) # convert image to HSV  
    cv2.imwrite(os.path.join(pic_path, '06_processing_image_as_hsv.jpg'), hsv) # save HSV file to show status, unnecessary for script to work
    
    # set ranges for blue and red to create masks, may need updating
    lower_blue = (100, 0, 0) # lower bound for each channel
    upper_blue = (255, 120, 175) # upper bound for each channel
    lower_red = (0, 100, 100) # lower bound for each channel
    upper_red = (100, 255, 255) # upper bound for each channel

    # create the mask and use it to change the colors
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    red_mask = cv2.inRange(hsv, lower_red, upper_red)
    
    # dilate resulting images to remove minor contours
    kernel = np.ones((7,7), np.uint8) # kernel for dilate function
    red_dilate = cv2.dilate(red_mask, kernel, iterations = 1) # dilate red
    blue_dilate = cv2.dilate(blue_mask, kernel, iterations = 1) #dilate blue
    cv2.imwrite(os.path.join(pic_path, '07_red_mask_dilated.jpg'), red_dilate) # save dilated red, unnecessary for script to work
    cv2.imwrite(os.path.join(pic_path, '08_blue_mask_dilated.jpg'), blue_dilate) # save dilated blue, unnecessary for script to work

    # process input variables
    r = int(round(r / 2)) # convert diameter to actual radius as int value
    safe_r = int(round(r*0.95)) # slightly lower radius to create a mask that removes contours from slight grid misplacement
    mask = np.zeros((2*r, 2*r), dtype = "uint8") # empty mask of grid cell size
    cv2.circle(mask, (r, r), safe_r, (255, 255, 255), -1) # circle for mask, centered with safe radius
    
    d = 0 # counter for filenames and cell numbers. Storing files is not necessary for script to work
    cell = [] # empty list for current state of cells
    
    # for loop that analyzes all grid cells
    for (x, y) in origins:
        d += 1 # increase counter by 1 for filenames
        
        # get region of interest (ROI) for red (geometry) and analyse number of contours (which identifies the markers) found
        roiGeo = red_dilate[y-r:y+r, x-r:x+r] # region on interest for cell number d
        maskedImgGeo = cv2.bitwise_and(roiGeo, roiGeo, mask = mask) # mask the ROI to eliminate adjacent grid cells
        im1, contoursGeo, hierarchy1 = cv2.findContours(maskedImgGeo,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE) # find contours within masked ROI
        cv2.drawContours(maskedImgGeo, contoursGeo, -1, (130,130,130), 3) # draw contours, not necessary for script to work
        
        # same as above for blue (ecotopes) as above
        roiEco = blue_dilate[y-r:y+r, x-r:x+r]
        maskedImgEco = cv2.bitwise_and(roiEco, roiEco, mask = mask)
        im2, contoursEco, hierarchy2 = cv2.findContours(maskedImgEco,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(maskedImgEco, contoursEco, -1, (130,130,130), 3)
        
        # store each analyzed ROI, not necessary for the script to work
        filenameGeo = 'geo_roi_%d.jpg'%d
        filenameEco = 'eco_roi_%d.jpg'%d
        cv2.imwrite(os.path.join(geo_path, filenameGeo), maskedImgGeo)
        cv2.imwrite(os.path.join(eco_path, filenameEco), maskedImgEco)
        
        """
        *** Voorlopig obsolete code i.v.m. wijziging direct naar cell lijst i.p.v. eerst in aparte list
        wegschrijven ***
        
        deze code fixed in dit geval de net missers (niet gesloten contouren), maar is niet robuust.
        Dit zit hem niet in de calbiratie, maar in de controle over licht. De gebruikte foto is slecht
        verlicht (donker), heeft reflectie en delen met schaduw. Volgende stap is het maken en updaten
        van foto's (spelstatus) testen, inclusief fysiek met speelstenen, verschillende invalshoeken
        en lichtinval.
        
        Bij gebruik van onderstaande regels wel de twee regels onder dit comment block weghalen.

        if len(contoursGeo) > 4:
            geometry.append(4)
        else:
            geometry.append(len(contoursGeo))
        if len(contoursEco) > 8:
            ecotopes.append(8)
        else:
            ecotopes.append(len(contoursEco))
        """
        
        cell.append([d, len(contoursGeo), len(contoursEco)])
    
    cell = np.array(cell) # convert list to a numpy array
    # export cell status to a text file
    with open(os.path.join(pic_path, '09_cell_status.txt'), 'w') as f:
        for item in cell:
            f.write("%s\n" % item)    

start = time.time() # start performance timer
filename = 'marker4.jpg'
canvas, thresh, pic_path = cali.detectCorners(filename) # image name for calibration (would be first image pre-session)
calibration = time.time() # calibration performance timer
pers, img_x, img_y, origins, radius = cali.rotateGrid(canvas, thresh, pic_path) # store calibration values as global variables
detectMarkers(filename, pers, img_x, img_y, origins, radius) # initiate the image processing function
end = time.time() # end performance timer
print('calibration time:', calibration-start) # print calibration performance time
print('image processing time:', end-calibration) # print image processing performance time
