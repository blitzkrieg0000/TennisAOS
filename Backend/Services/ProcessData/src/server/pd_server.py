import logging
from libs.canvasTools import extractSpecialLocations
from libs.scoreTools import get_score
from concurrent import futures
import pickle

import grpc
import processData_pb2 as rc
import processData_pb2_grpc as rc_grpc
import cv2
import numpy as np

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

class PDServer(rc_grpc.ProcessDataServicer):

    def __init__(self):
        pass
    
    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)

    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)

    def Bytes2Frame(self, image):
        nparr = np.frombuffer(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
        
    def Frame2Bytes(self, image):
        res, encodedImg = cv2.imencode('.jpg', image)
        frame = encodedImg.tobytes()
        return frame

    def processAOS(self, request, context):
        frame = self.Bytes2Frame(request.frame) 
        data = self.Bytes2Obj(request.data)

        canvas = frame.copy()
        line_data, point_area_data, canvas = extractSpecialLocations(courtLines=data["court_lines"], canvas=canvas, AOS_TYPE=data["court_point_area_id"])
        
        selected_point = [0, 0]
        selected_point = max(data["fall_point"], key=lambda x:x[1])
        score = get_score(point_area_data, selected_point)
        
        responseData = {}
        responseData["score"] = score
        responseData["line_data"] = line_data
        responseData["point_area_data"] = point_area_data

        return rc.processAOSResponse(data=self.Obj2Bytes(responseData), frame=self.Frame2Bytes(canvas))


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_ProcessDataServicer_to_server(PDServer(), server)
    server.add_insecure_port('[::]:50024')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()