from __future__ import print_function

import logging
import time

import grpc

import clients.StreamKafka.Consumer.kafkaConsumer_pb2 as rc
import clients.StreamKafka.Consumer.kafkaConsumer_pb2_grpc as rc_grpc

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)


class KafkaConsumerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50032')
        self.stub = rc_grpc.kafkaConsumerStub(self.channel)

    def consumer(self, topicName, groupName, limit=-1):
        requestData = rc.ConsumerRequest(topicName=topicName, group=groupName, limit=limit)
        return self.stub.consumer(requestData)

    def disconnect(self):
        self.channel.close()

if "__main__" == __name__:

    kcm  = KafkaConsumerManager()
    gen = kcm.consumer(topicName="deneme", groupName="test-1", limit=-1)
    for item in gen:
        byte_data = item.data
        print(byte_data[:20])
        time.sleep(5)