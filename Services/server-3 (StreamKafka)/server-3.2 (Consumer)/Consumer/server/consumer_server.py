from concurrent import futures

import grpc
import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc
from libs.KafkaConsumerManager import KafkaConsumerManager
from libs.helpers import Converters
import logging

class CKConsumer(rc_grpc.kafkaConsumerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaConsumerManager = KafkaConsumerManager()

    def consumer(self, request, context):
        topicName = request.topicName
        groupName = request.group
        limit = request.limit

        CONSUMER_GENERATOR = self.kafkaConsumerManager.consumer(topics=[topicName], consumerGroup=groupName, offsetMethod="earliest", limit=limit)
        for data in CONSUMER_GENERATOR:
            yield rc.ConsumerResponse(data=data)

    def getRunningConsumers(self, request, context):
        return rc.getRunningConsumersResponse(data=Converters.obj2bytes(self.kafkaConsumerManager.getRunningConsumers()))

    def stopAllRunningConsumers(self):
        self.kafkaConsumerManager.stopAllRunningConsumers()
        return rc.stopAllRunningConsumersResponse(data="TRYING...")

    def stopRunningCosumer(self, request, context): #TopicName
        self.kafkaConsumerManager.stopRunningCosumer(request.data)
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