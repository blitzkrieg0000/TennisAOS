import cv2
import numpy as np

canvas = cv2.imread("TEST/test.jpg")

def frame2bytes(frame):
    res, encodedImg = cv2.imencode('.jpg', frame)
    return encodedImg.tobytes()

def bytes2frame(image):
    nparr = np.frombuffer(image, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame

byte_frame = frame2bytes(canvas)
frame = bytes2frame(byte_frame)

print(frame)
