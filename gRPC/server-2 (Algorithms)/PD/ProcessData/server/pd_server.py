from libs.logger import logger
from libs.canvasTools import extractSpecialLocations
from libs.scoreTools import get_score
from concurrent import futures
import pickle

import grpc
import processData_pb2 as rc
import processData_pb2_grpc as rc_grpc
import cv2
import numpy as np

class PDServer(rc_grpc.ProcessDataServicer):

    def __init__(self):
        pass
    
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2img(self, image):
        nparr = np.frombuffer(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
        
    def img2bytes(self, image):
        res, encodedImg = cv2.imencode('.jpg', image)
        frame = encodedImg.tobytes()
        return frame

    def processAOS(self, request, context):
        frame = self.bytes2img(request.frame) 
        data = self.bytes2obj(request.data)

        canvas = frame.copy()
        line_data, point_area_data, canvas = extractSpecialLocations(courtLines=data["court_lines"], canvas=canvas, AOS_TYPE=data["aos_type"])
        score = get_score(point_area_data, data["fall_point"])
        
        responseData = {}
        responseData["score"] = score
        responseData["line_data"] = line_data
        responseData["point_area_data"] = point_area_data

        return rc.processAOSResponse(data=self.obj2bytes(responseData), frame=self.img2bytes(canvas))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_ProcessDataServicer_to_server(PDServer(), server)
    server.add_insecure_port('[::]:50024')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()