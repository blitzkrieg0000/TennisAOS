from __future__ import print_function
import grpc
import clients.TrackBall.trackBall_pb2 as rc
import clients.TrackBall.trackBall_pb2_grpc as rc_grpc

class TBClient():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50022') #trackballservice
        self.stub = rc_grpc.trackBallStub(self.channel)
    
    def findTennisBallPosition(self, data, name):
        requestData = rc.trackBallRequest(tensor=data, name=name)
        responseData = self.stub.findTennisBallPosition(requestData)
        return responseData.point

    def deleteDetector(self, name):
        requestData = rc.deleteDetectorRequest(data=name)
        responseData = self.stub.deleteDetector(requestData)
        return responseData.data

    def disconnect(self):
        self.channel.close()