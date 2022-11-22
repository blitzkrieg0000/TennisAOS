from __future__ import print_function
import pickle

import grpc
import processData_pb2 as rc
import processData_pb2_grpc as rc_grpc
import cv2
import numpy as np

class PDClient():
    def __init__(self):
        self.channel = grpc.insecure_channel('processdataservice:50024')
        self.stub = rc_grpc.ProcessDataStub(self.channel)
    
    def bytes2img(self, image):
        nparr = np.frombuffer(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
        
    def img2bytes(self, image):
        res, encodedImg = cv2.imencode('.jpg', image)
        frame = encodedImg.tobytes()
        return frame

    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)

    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)

    def processAOS(self, image, data):
        requestData = rc.processAOSRequest(data=self.Obj2Bytes(data), frame=self.img2bytes(image))
        responseData = self.stub.processAOS(requestData)
        frame = responseData.frame
        resData = responseData.data
        return frame, resData

    def disconnect(self):
        self.channel.close()