from __future__ import print_function
import pickle
import grpc

import clients.PredictFallPosition.predictFallPosition_pb2 as rc
import clients.PredictFallPosition.predictFallPosition_pb2_grpc as rc_grpc

class PFPClient():
    def __init__(self):
        self.channel = grpc.insecure_channel('predictfallpositionservice:50023')
        self.stub = rc_grpc.predictFallPositionStub(self.channel)
    
    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def predictFallPosition(self, points):
        requstData = rc.predictFallPositionControllerRequest(points=self.obj2bytes(points))
        response = self.stub.predictFallPositionController(requstData)
        return response.points

    def disconnect(self):
        self.channel.close()