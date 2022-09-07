from __future__ import print_function
import grpc
import clients.StreamKafka.Consumer.kafkaConsumer_pb2 as rc
import clients.StreamKafka.Consumer.kafkaConsumer_pb2_grpc as rc_grpc
import numpy as np
import cv2

import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)
class KafkaConsumerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50032') #consumerservice
        self.stub = rc_grpc.kafkaConsumerStub(self.channel)

    def bytes2frame(self, byte_img ):
        nparr = np.frombuffer(byte_img, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
        return frame

    def consumer(self, topicName, groupName, limit=-1, show=False):
        requestData = rc.ConsumerRequest(topicName=topicName, group=groupName, limit=limit)
        return self.stub.consumer(requestData)

    def getRunningConsumers(self):
        responseData = self.stub.getRunningConsumers(rc.getRunningConsumersRequest(data=""))
        return responseData.data

    def stopAllRunningConsumers(self):
        message = self.stub.stopAllRunningConsumers(rc.stopAllRunningConsumersRequest(data=""))
        return message.data

    def stopRunningCosumer(self, consumer_topic_name):
        message = self.stub.stopRunningCosumer(rc.stopRunningCosumerRequest(data=consumer_topic_name))
        return message.data

    def disconnect(self):
        self.channel.close()