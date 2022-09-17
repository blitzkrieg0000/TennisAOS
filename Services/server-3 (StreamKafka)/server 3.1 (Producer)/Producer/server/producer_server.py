import logging
import pickle
from concurrent import futures

import grpc

import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.helpers import EncodeManager
from libs.KafkaProducerManager import KafkaProducerManager
from libs.Response import Response, ResponseCodes

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)


class CKProducer(rc_grpc.kafkaProducerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaProducerManager = KafkaProducerManager()

    def producer(self, request, context):
        requestData = EncodeManager.deserialize(request.data)
        response = self.kafkaProducerManager.startProducer(requestData, context)
        if(response.code==ResponseCodes.SUCCESS):
            responseData = rc.producerResponse(result=response.data, process_name=requestData["topicName"])
        else:
            context.set_code(grpc.StatusCode.CANCELLED)
            context.set_details('Başarısız.')
            return rc.producerResponse()
        return responseData

    def getAllProducerProcesses(self, request, context):
        response = self.kafkaProducerManager.getAllProducerProcesses()
        if(response.code==ResponseCodes.SUCCESS):
            return rc.getAllProducerProcessesResponse(data=EncodeManager.serialize(response.data))
        return rc.getAllProducerProcessesResponse()

    def stopProducer(self, request, context):
        response = self.kafkaProducerManager.stopProducerProcess(request.process_name)
        if(response.code==ResponseCodes.SUCCESS):
            responseData = rc.stopProducerResponse(result=response.data)
        else:
            responseData = rc.stopProducerResponse()

        return responseData

    def stopAllProducerProcesses(self, request, context):
        response = self.kafkaProducerManager.stopAllProducerProcesses()
        if(response.code==ResponseCodes.SUCCESS):
            responseData = rc.stopAllProducerProcessesResponse(result=response.data)
        else:
            responseData = rc.stopAllProducerProcessesResponse()

        return responseData


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaProducerServicer_to_server(CKProducer(), server)
    server.add_insecure_port('[::]:50031')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

