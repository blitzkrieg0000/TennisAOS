import inspect
import os

import cv2


def CWD():
    """Bu fonksiyonu çağıran dosyanın konumunu al"""
    p = "/"
    try: p = os.path.abspath(os.path.dirname(inspect.stack()[1][1]))
    except Exception as e: pass
    return p


def ResizeWRTRatio(frame, aspect_ratio_w=16, aspect_ratio_h=9, ratio=-89) -> (tuple[cv2.Mat, float]):
    if frame is None:
        raise AssertionError("Frame: None")

    h, w, c = frame.shape
    canvas = frame.copy()
    scalingRatio = 1

    if w<aspect_ratio_w or h<aspect_ratio_h:
        raise AssertionError("AspectRatio oranları verilen giriş frame'i boyutunu aşıyor.")

    k = w/aspect_ratio_w
    new_k = k+ratio

    if new_k<=0 or new_k == k:
        return canvas, scalingRatio

    scalingRatio = k/new_k
    new_w = new_k*aspect_ratio_w
    new_h = new_k*aspect_ratio_h
    canvas = cv2.resize(canvas, (int(new_w), int(new_h)))

    return canvas, scalingRatio
