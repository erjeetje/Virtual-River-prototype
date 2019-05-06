# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 12:13:54 2019

@author: HaanRJ
"""

import cv2


def show_webcam(mirror=False):
    cam = cv2.VideoCapture(0)  # 0 or 1, always 0 if built-in webcam disabled
    if cam:
        print("found a camera")
    else:
        print("no camera found")
    cam.set(3, 1920)
    cam.set(4, 1080)
    #time.sleep(2)
    #cv2.startWindowThread()
    #cv2.namedWindow("my webcam")
    ret_val, img = cam.read()
    cv2.imwrite('webcam_matte_stickers3.jpg', img)
    while True:
        ret_val, img = cam.read()
        if img.any():
            if mirror:
                img = cv2.flip(img, 1)
            cv2.imshow('my webcam', img)
        else:
            continue
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    cv2.destroyAllWindows()


def main():
    show_webcam(mirror=True)


if __name__ == '__main__':
    main()
