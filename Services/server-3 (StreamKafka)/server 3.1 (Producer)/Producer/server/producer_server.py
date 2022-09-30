import logging
import multiprocessing
import time
from concurrent import futures

import grpc

import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.helpers import EncodeManager
from libs.KafkaProducerManager import KafkaProducerManager
from libs.Response import *

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)

import signal
from signal import SIG_DFL, SIGPIPE

signal.signal(SIGPIPE,SIG_DFL) 


class CKProducer(rc_grpc.kafkaProducerServicer):
    
    def __init__(self): 
        super().__init__()
        self.kafkaProducerManager = KafkaProducerManager()


    def CreateResponse(self, response:Response):
        return rc.Response(Code=rc.Response.ResponseCodes.Value(response.code.name), Message=response.message, Data=response.data)


    def producer(self, requestIter, context):
        requestData = next(requestIter)
        qq = multiprocessing.Manager().Queue(maxsize=3)
        arr = {
            "topicName" : requestData.TopicName,
            "source" : requestData.Source,
            "isVideo" : requestData.IsVideo,
            "limit" : requestData.Limit,
            "errorLimit" : requestData.ErrorLimit
        }
        
        self.kafkaProducerManager.startProducer(arr, qq)

        while context.is_active() or requestData.Independent:

            tic = time.time()
            frame = qq.get(block=True)
            toc = time.time()
            logging.warning("get: "+str(toc-tic))

            yield rc.ProducerResponse(
                Response=self.CreateResponse(
                    Response(ResponseCodes.SUCCESS, message="", data=frame)
                )
            )

            #bidirectional empty
            if not requestData.Independent:
                request = next(requestIter)


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

