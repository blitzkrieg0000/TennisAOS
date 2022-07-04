from __future__ import print_function
from libs.logger import logger
import pickle
import grpc
import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc

class KafkaProducerManager():

    def __init__(self):
        self.channel = grpc.insecure_channel('producerservice:50031')
        self.stub = rc_grpc.kafkaProducerStub(self.channel)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def startProduce(self, topicName, streamUrl, limit=-1):
        requestData = rc.producerRequest(topicName=topicName, streamName=streamUrl, limit=limit)
        response = self.stub.producer(requestData)
        logger.info(f"RESULTS: {response.result} \n THREAD_NAME: {response.thread_name}")
        return response.thread_name

    def getProducerThreads(self):
        requestData = rc.getProducerThreadsRequest(data="True")
        responseData = self.stub.getProducerThreads(requestData)
        return responseData.data

    def stopAllProducerThreads(self):
        requestData=rc.stopAllProducerThreadsRequest(data="True")
        responseData = self.stub.stopAllProducerThreads(requestData)
        return responseData

    def stopProduce(self, thread_name):        
        requestData = rc.stopProduceRequest(thread_name=thread_name)
        response = self.stub.stopProduce(requestData)
        logger.info(f"RESULTS: {response.result}")
    
    def deleteTopics(self, topicNames):
        requestData = rc.deleteTopicsRequest(data=self.obj2bytes(topicNames))
        responseData = self.stub.deleteTopics(requestData)
        return responseData.data

    def disconnect(self):
        self.channel.close()