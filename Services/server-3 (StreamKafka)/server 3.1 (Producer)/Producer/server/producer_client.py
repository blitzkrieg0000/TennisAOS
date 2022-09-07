from __future__ import print_function
import pickle
import time
import grpc
import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.helpers import EncodeManager


class KafkaProducerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50031') #producerservice:50031
        self.stub = rc_grpc.kafkaProducerStub(self.channel)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def producer(self, data):
        requestData = rc.producerRequest(data=EncodeManager.serialize(data))
        response = self.stub.producer(requestData)
        return response.process_name

    def getAllProducerProcesses(self):
        requestData = rc.getAllProducerProcessesRequest(data="")
        responseData = self.stub.getAllProducerProcesses(requestData)
        return responseData.data

    def stopAllProducerProcesses(self):
        requestData=rc.stopAllProducerProcessesRequest(data="")
        responseData = self.stub.stopAllProducerProcesses(requestData)
        return responseData.result

    def stopProducer(self, process_name):        
        requestData = rc.stopProducerRequest(process_name=process_name)
        responseData = self.stub.stopProducer(requestData)
        return responseData.result
    
    def disconnect(self):
        self.channel.close()