from concurrent import futures
import pickle

import grpc
import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc
from libs.kafka_manager import KafkaManager
import logging

class CKConsumer(rc_grpc.kafkaConsumerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaManager = KafkaManager()

    def obj2bytes(self, obj):
        return pickle.dumps(obj)
        
    def consumer(self, request, context):
        topicName = request.topicName
        groupName = request.group
        limit = request.limit

        CONSUMER_GENERATOR = self.kafkaManager.consumer(topics=[topicName], consumerGroup=groupName, offsetMethod="earliest", limit=limit)
        for data in CONSUMER_GENERATOR:
            yield rc.ConsumerResponse(data=data)

    def getRunningConsumers(self, request, context):
        return rc.getRunningConsumersResponse(data=self.obj2bytes(self.kafkaManager.getRunningConsumers()))

    def stopAllRunningConsumers(self):
        self.kafkaManager.stopAllRunningConsumers()
        return rc.stopAllRunningConsumersResponse(data="TRYING...")

    def stopRunningCosumer(self, request, context): #TopicName
        self.kafkaManager.stopRunningCosumer(request.data)
        return rc.stopAllRunningConsumersResponse(data="TRYING...")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaConsumerServicer_to_server(CKConsumer(), server)
    server.add_insecure_port('[::]:50032')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)
    serve()