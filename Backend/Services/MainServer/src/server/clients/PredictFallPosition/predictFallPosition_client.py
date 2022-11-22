from __future__ import print_function
import pickle
import grpc

import clients.PredictFallPosition.predictFallPosition_pb2 as rc
import clients.PredictFallPosition.predictFallPosition_pb2_grpc as rc_grpc

class PFPClient():
    def __init__(self):
        self.channel = grpc.insecure_channel('predictfallpositionservice:50023') #predictfallpositionservice
        self.stub = rc_grpc.predictFallPositionStub(self.channel)
    
    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)

    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)

    def predictFallPosition(self, points):
        requstData = rc.predictFallPositionControllerRequest(points=self.Obj2Bytes(points))
        response = self.stub.predictFallPositionController(requstData)
        return response.points

    def disconnect(self):
        self.channel.close()