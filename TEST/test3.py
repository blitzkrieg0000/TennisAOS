import cv2

file = open("TEST/imagebyte.txt", "w")

res = cv2.imread("TEST/test.jpg")

res, encodedImg = cv2.imencode('.jpg', res)

file.write(str(encodedImg.tobytes()))

file.close()