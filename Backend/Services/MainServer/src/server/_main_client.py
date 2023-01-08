import grpc
import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc


class MainServerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50011')
        self.stub = rc_grpc.MainServerStub(self.channel)


    def StartProcess(self, id):
        requestData = rc.StartProcessRequestData(ProcessId=id)
        responseData = self.stub.StartProcess(requestData)
        return responseData


    def MergeData(self, processId):
        requestData = rc.MergeDataRequestData(ProcessId=processId)
        responseData = self.stub.MergeData(requestData)
        return responseData


    def disconnect(self):
        self.channel.close()



if __name__ == "__main__":
    msm = MainServerManager()
    response = msm.MergeData(900)
