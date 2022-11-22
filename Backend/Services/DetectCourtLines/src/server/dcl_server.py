import logging
from concurrent import futures
import pickle

import grpc
import detectCourtLines_pb2 as rc
import detectCourtLines_pb2_grpc as rc_grpc
from libs.point_tools import CourtDetector

import cv2
import numpy as np

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

class DCLServer(rc_grpc.detectCourtLineServicer):

    def __init__(self):
        #TODO objenin sıfırlanması gerekiyor: v2
        self.court_detector = CourtDetector()
    
    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)

    def extractCourtLines(self, request, context):
        court_detector = CourtDetector()
        nparr = np.frombuffer(request.frame, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        logging.info("Saha tespit ediliyor...\n")
        canvas_image = court_detector.detect(frame.copy())
        court_points = []
        warp_matrix = None
        if court_detector.success_flag:
            logging.info("Saha Tespiti Başarılı !")
            court_points = court_detector.saved_lines
            if len(court_detector.court_warp_matrix)>0:
                warp_matrix = court_detector.court_warp_matrix[-1]
        else:
            logging.info("Saha Tespiti Başarısız !")

        court_points = list(court_points)
        return rc.extractCourtLinesResponse(point=self.Obj2Bytes([court_points, warp_matrix]))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_detectCourtLineServicer_to_server(DCLServer(), server)
    server.add_insecure_port('[::]:50021')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()