# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 12:13:54 2019

@author: HaanRJ
"""

import cv2


def get_image(turn, mirror=False):
    """
    Method to get an image from the camera. Activates the webcam, makes sure
    the camera is set to fullHD and takes a picture. The picture is stored for
    reference and backup. i stands for turn.
    """
    cam = cv2.VideoCapture(0)  # 0 or 1, always 0 if built-in webcam disabled
    if cam:
        print("found a camera")
    else:
        print("no camera found")
    cam.set(3, 1920)
    cam.set(4, 1080)
    ret_val, img = cam.read()
    filename = 'turn_picture%i.jpg' % turn
    cv2.imwrite(filename, img)
    return img


def main():
    get_image(mirror=True)


if __name__ == '__main__':
    main()
