from __future__ import print_function
import pickle

import grpc
import clients.ProcessData.processData_pb2 as rc
import clients.ProcessData.processData_pb2_grpc as rc_grpc
import cv2
import numpy as np

class PDClient():
    def __init__(self):
        self.channel = grpc.insecure_channel('processdataservice:50024') #processdataservice
        self.stub = rc_grpc.ProcessDataStub(self.channel)
    
    def bytes2img(self, image):
        nparr = np.frombuffer(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
        
    def img2bytes(self, image):
        res, encodedImg = cv2.imencode('.jpg', image)
        frame = encodedImg.tobytes()
        return frame

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def processAOS(self, image, data):
        requestData = rc.processAOSRequest(frame=image, data=self.obj2bytes(data))
        responseData = self.stub.processAOS(requestData)
        return responseData.frame, responseData.data

    def disconnect(self):
        self.channel.close()