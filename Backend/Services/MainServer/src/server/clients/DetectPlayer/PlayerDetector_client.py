import logging

import clients.DetectPlayer.conf.PlayerDetector_pb2 as rc
import clients.DetectPlayer.conf.PlayerDetector_pb2_grpc as rc_grpc
import grpc
from clients.DetectPlayer.lib.helper import Converters

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


MAX_MESSAGE_LENGTH = 15*1024*1024
class PlayerDetectorClient():
    def __init__(self) -> None:
        self.channel = grpc.insecure_channel('playerdetectorservice:50081', 
                    options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ],
            # compression=grpc.Compression.Gzip
        )
        self.stub = rc_grpc.PlayerDetectorStub (self.channel)
        

    def Detect(self, frame):
        """
            return:
                .Response.Code: Enum[ResponseCodes: pb_Enum]
                .Response.Message: string
                .Response.Data: bytes => List[[top_left_x, top_left_y, bottom_right_x, bottom_right_y, confidence, class_number]]
        """
        byteFrame, h, w, c = Converters.Ndarray2Bytes(frame)
        return self.stub.Detect(rc.DetectRequest(Frame=rc.Frame(Bytes=byteFrame, H=h, W=w, C=c)))


    def disconnect(self):
        self.channel.close()



