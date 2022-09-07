import logging
import pickle
from concurrent import futures

import grpc

import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.helpers import EncodeManager
from libs.KafkaProducerManager import KafkaProducerManager

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)


class CKProducer(rc_grpc.kafkaProducerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaProducerManager = KafkaProducerManager()

    def producer(self, request, context):
        requestData = EncodeManager.deserialize(request.data)
        msg = self.kafkaProducerManager.startProducer(requestData)
        responseData = rc.producerResponse(result=msg, process_name=requestData["topicName"])
        return responseData

    def getAllProducerProcesses(self, request, context):
        processes = EncodeManager.serialize(self.kafkaProducerManager.getAllProducerProcesses())
        return rc.getAllProducerProcessesResponse(data=processes)

    def stopProducer(self, request, context):
        msg = self.kafkaProducerManager.stopProducerProcess(request.process_name)
        responseData = rc.stopProducerResponse(result=msg)
        return responseData

    def stopAllProducerProcesses(self, request, context):
        msg = self.kafkaProducerManager.stopAllProducerProcesses()
        responseData = rc.stopAllProducerProcessesResponse(result=msg)
        return responseData


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaProducerServicer_to_server(CKProducer(), server)
    server.add_insecure_port('[::]:50031')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

