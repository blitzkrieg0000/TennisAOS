    
import base64
import cv2

img = cv2.imread("TEST/test.jpg")


def frame2base64(frame):
    etval, buffer = cv2.imencode('.png', frame)
    return base64.b64encode(buffer).decode()


result = frame2base64(img)

f = open("TEST/temp.txt", "a")
f.write(result)
f.close()