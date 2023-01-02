import logging

import cv2
from libs.courtDetector import CourtDetector
from libs.helper import CWD

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

court_detector = CourtDetector(         # Setting1, Setting2
        threshold_value=25,             # 160, 25
        resizing_ratio=-120,            # -80, -120
        pp_gaussian_blur=True,          # True, True
        max_line_gap=10,                # 10, 10
        min_line_length=110,            # 100, 110
        edge_detection_method="Robert"  # None, "Robert"
    )

file_name = "court02"
frame = cv2.imread(CWD() + f"/asset/image/{file_name}.png")

lines = court_detector.Detect(frame)
canvasImage = court_detector.DrawCourtLines()

if canvasImage is not None:
    cv2.imshow('', canvasImage)
    cv2.waitKey(0)
    cv2.imwrite(CWD() + f"/asset/image/{file_name}_result.jpg", canvasImage)