from __future__ import print_function
import grpc
import testServer_pb2 as rc
import testServer_pb2_grpc as rc_grpc

class MainClient():
    def __init__(self):
        self.channel = grpc.insecure_channel("localhost:9999") # MAIN-SERVICE-DEPLOYMENT-IP TODO: NODEPORT İLE DIŞARI AÇILACAK TEK BİR DEPLOYMENTA BU ŞEKİLDE BAĞLANILMAYACAK
        self.stub = rc_grpc.TestServerStub(self.channel)

    def Process(self):
        requestData = rc.requestData(data="")
        responseData = self.stub.Process(requestData)
        return responseData

    def disconnect(self):
        self.channel.close()


if __name__ == "__main__":
    client = MainClient()
    message = client.Process()
    print(message.data)
