from __future__ import print_function
import logging
import pickle
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
        logging.info(f"RESULTS: {response.result}")
    
    def deleteTopics(self, topicNames):
        requestData = rc.deleteTopicsRequest(data=self.obj2bytes(topicNames))
        responseData = self.stub.deleteTopics(requestData)
        return responseData.data

    def disconnect(self):
        self.channel.close()


if "__main__" == __name__:
    client = KafkaProducerManager()
    data = {}
    data["topicName"] = "deneme"
    data["streamUrl"] = "/assets/en_yeni.mp4"
    data["is_video"] = True
    data["limit"] = -1

    client.producer(data)
