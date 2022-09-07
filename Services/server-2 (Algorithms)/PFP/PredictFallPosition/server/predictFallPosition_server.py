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
        window_length = 5
        for i in range(15):
            sp = StatusPredicter()
            predicted_points = sp.predictFallBallPositon(points, window=window_length)
            if predicted_points is not None and len(predicted_points) == 1:
                break
            window_length+=3
            if window_length%2 == 0:
                window_length = window_length + 1

        return rc.predictFallPositionControllerResponse(points=self.obj2bytes(predicted_points))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_predictFallPositionServicer_to_server(PFPServer(), server)
    server.add_insecure_port('[::]:50023')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()