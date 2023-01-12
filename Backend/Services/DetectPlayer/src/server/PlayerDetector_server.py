import logging
from concurrent import futures

import conf.PlayerDetector_pb2 as rc
import conf.PlayerDetector_pb2_grpc as rc_grpc
import grpc
from lib.detect import ObjectDetector
from lib.helper import CWD, Converters
from lib.Response import CreateResponse, ResponseCodes

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


MAX_MESSAGE_LENGTH = 15*1024*1024
class PlayerDetectorServer(rc_grpc.PlayerDetectorServicer):
    def __init__(self):
        super().__init__()
        self.objectDetector = ObjectDetector(
            CWD() + "/lib/weight/onnx/yolov7.onnx",
            conf_thres=0.35,
            iou_thres=0.45,
            classes=[0]
        )



    def Detect(self, request, context):
        frame = Converters.Bytes2Ndarray(request.Frame.Bytes, request.Frame.H, request.Frame.W, request.Frame.C)
        
        detectedObject, _ = self.objectDetector.Detect(frame)
        
        response = rc.DetectResponse(
            Response=CreateResponse(rc)(ResponseCodes.SUCCESS, message="", data=Converters.Obj2Bytes(detectedObject))
        )

        return response



def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
        ],
        # compression=grpc.Compression.Gzip
    )

    rc_grpc.add_PlayerDetectorServicer_to_server(PlayerDetectorServer(), server)
    server.add_insecure_port('[::]:50081')
    server.start()
    server.wait_for_termination()



if __name__ == "__main__":
    serve()

