    
import base64
import cv2

img = cv2.imread("TEST/test.jpg")


def frame2base64(frame):
    etval, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer)


result = frame2base64(img)

print(result)


f = open("temp.txt", "a")
f.write("Now the file has more content!")
f.close()

