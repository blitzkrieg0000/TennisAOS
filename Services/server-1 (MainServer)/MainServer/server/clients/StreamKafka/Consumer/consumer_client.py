from __future__ import print_function

import logging
import time

import grpc

import clients.StreamKafka.Consumer.kafkaConsumer_pb2 as rc
import clients.StreamKafka.Consumer.kafkaConsumer_pb2_grpc as rc_grpc

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)


class KafkaConsumerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('consumerservice:50032') #consumerservice
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