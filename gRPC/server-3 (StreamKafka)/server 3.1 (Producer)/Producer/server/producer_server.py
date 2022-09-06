from concurrent import futures
import pickle

import grpc
from libs.helpers import Converters, EncodeManager
import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.kafka_manager import KafkaProducerManager

import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)
class CKProducer(rc_grpc.kafkaProducerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaManager = KafkaProducerManager()
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def producer(self, request, context):
        requestData = EncodeManager.deserialize(request.data)
        msg = self.kafkaManager.startProducer(requestData)
        responseData = rc.producerResponse(result=msg, process_name=requestData["process_name"])
        return responseData

    def getAllProducerProcesses(self, request, context):
        th = Converters.obj2bytes(self.kafkaManager.getAllProducerProcesses())
        return rc.getAllProducerProcessesResponse(data=th)

    def stopProducer(self, request, context):
        process_name = request.process_name
        msg = self.kafkaManager.stopProducerProcesses(process_name)
        responseData = rc.stopProducerResponse(result=msg)
        return responseData

    def stopAllProducerProcess(self, request, context):
        msg = self.kafkaManager.stopAllProducerProcess()
        responseData = rc.stopAllProducerProcessesResponse(data=msg)
        return responseData

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaProducerServicer_to_server(CKProducer(), server)
    server.add_insecure_port('[::]:50031')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
