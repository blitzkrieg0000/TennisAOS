from concurrent import futures
import pickle

import grpc
import predictFallPosition_pb2 as rc
import predictFallPosition_pb2_grpc as rc_grpc

from libs.statusPredicter import StatusPredicter

class PFPServer(rc_grpc.predictFallPositionServicer):

    def __init__(self):
        pass
        
    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def predictFallPositionController(self, request, context):
        points = self.bytes2obj(request.points)
        sp = StatusPredicter()
        predicted_points = sp.predictFallBallPositon(points)
        return rc.predictFallPositionControllerResponse(points=self.obj2bytes(predicted_points))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_predictFallPositionServicer_to_server(PFPServer(), server)
    server.add_insecure_port('[::]:50023')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()