import logging
import pickle
from concurrent import futures

import cv2
import grpc
import numpy as np

import trackBall_pb2 as rc
import trackBall_pb2_grpc as rc_grpc
from libs.trackNet_onnx import TrackNetObjectDetection

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)
class TBServer(rc_grpc.trackBallServicer):

    def __init__(self):
        #TODO objenin sıfırlanması gerekiyor: v2
        self.detectors = {}
    
    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def findTennisBallPosition(self, request, context):
        
        nparr = np.frombuffer(request.tensor, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if not request.name in self.detectors.keys():
            self.detectors[request.name] = TrackNetObjectDetection()
        
        (draw_x, draw_y), canvas = self.detectors[request.name].detect(frame, draw=True)
        return rc.trackBallResponse(point=self.obj2bytes([draw_x, draw_y]))

    def deleteDetector(self, request, context):
        if request.data in self.detectors.keys():
            self.detectors.pop(request.data)
        return rc.deleteDetectorResponse(data="OK")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_trackBallServicer_to_server(TBServer(), server)
    server.add_insecure_port('[::]:50022')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
