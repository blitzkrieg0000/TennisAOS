from __future__ import print_function

import logging
import time

import grpc

import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


class KafkaConsumerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50032')
        self.stub = rc_grpc.kafkaConsumerStub(self.channel)

    def consumer(self, topicName, groupName, limit=-1, offsetMethod="earliest"):
        requestData = rc.ConsumerRequest(topicName=topicName, group=groupName, limit=limit, offsetMethod=offsetMethod)
        return self.stub.consumer(requestData)

    def getAllConsumers(self):
        responseData = self.stub.getAllConsumers(rc.getAllConsumersRequest(data=""))
        return responseData.data

    def stopConsumer(self, topic_name):
        responseData = self.stub.stopConsumer(rc.stopConsumerRequest(data=topic_name))
        return responseData.result

    def stopAllConsumers(self):
        responseData = self.stub.stopAllConsumers(rc.stopAllConsumersRequest(data=""))
        return responseData.result

    def disconnect(self):
        self.channel.close()

if "__main__" == __name__:

    kcm  = KafkaConsumerManager()
    gen = kcm.consumer(topicName="deneme", groupName="test-7", limit=-1)
    for i,item in enumerate(gen):
        byte_data = item.data
        print(i,"-->",byte_data[:10])
        time.sleep(1)