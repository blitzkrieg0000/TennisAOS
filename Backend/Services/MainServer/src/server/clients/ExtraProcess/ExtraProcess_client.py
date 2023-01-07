from clients.ExtraProcess.lib.helpers import Converters
import clients.ExtraProcess.conf.ExtraProcess_pb2 as rc
import clients.ExtraProcess.conf.ExtraProcess_pb2_grpc as rc_grpc
import grpc


MAX_MESSAGE_LENGTH = 10*1024*1024

class ExtraProcessClient():
    def __init__(self):
        self.channel = grpc.insecure_channel(
            'extraprocessservice:50071',
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ],
            # compression=grpc.Compression.Gzip
        )
        self.stub = rc_grpc.ExtraProcessStub(self.channel)
    

    def MergeData(self, data):
        response = self.stub.MergeData(rc.ExtraProcessRequest(Data=data))
        return response


    def Disconnect(self):
        self.channel.close()            # compression=grpc.Compression.Gzip