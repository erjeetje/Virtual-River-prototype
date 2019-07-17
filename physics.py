import numpy as np
import cv2

def warp_flow(img, flow):
    """transform image with flow field"""
    h, w = flow.shape[:2]
    flow = -flow
    flow[:, :, 0] += np.arange(w)
    flow[:, :, 1] += np.arange(h)[:, np.newaxis]
    #res = cv2.remap(img, flow, None, cv2.INTER_LINEAR,
    #                borderValue=(1.0, 1.0, 1.0, 0.0))
    res = cv2.remap(img, flow, None, cv2.INTER_LINEAR,
                    borderValue=(0.0, 0.0, 0.0, 0.0))
    return res
