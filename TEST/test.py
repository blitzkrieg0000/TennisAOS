import cv2
import base64
import numpy as np
canvas = cv2.imread("TEST/test.jpg")

encoded_string = base64.b64encode(canvas.tobytes())

