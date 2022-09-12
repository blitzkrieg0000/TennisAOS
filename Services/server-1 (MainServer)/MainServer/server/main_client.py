from __future__ import print_function
import pickle
import grpc
import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc

class MainServerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50011') #redisservice:50051
        self.stub = rc_grpc.MainServerStub(self.channel)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def StartProcess(self, id):
        requestData = rc.StartProcessRequestData(ProcessId=id)
        responseData = self.stub.StartProcess(requestData)
        return responseData

    def disconnect(self):
        self.channel.close()


if __name__ == "__main__":
    msm = MainServerManager()
    response = msm.StartProcess(118)
    print(response.Message)