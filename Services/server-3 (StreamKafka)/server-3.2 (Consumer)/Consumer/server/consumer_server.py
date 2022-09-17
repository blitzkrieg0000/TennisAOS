from concurrent import futures

import grpc
import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc
from libs.KafkaConsumerManager import KafkaConsumerManager
from libs.helpers import EncodeManager
import logging


class CKConsumer(rc_grpc.kafkaConsumerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaConsumerManager = KafkaConsumerManager()
        self.consumers = {}
    
    def __removeConsumer(self, topicName):
        if topicName in self.consumers.keys():
            try: self.consumers.pop(topicName)
            except: pass

    def getAllConsumers(self, request, context):
        return rc.getAllConsumersResponse(data=EncodeManager.serialize(list(self.consumers.keys())))

    def stopConsumer(self, request, context):
        self.consumer[request.data] = False

    def stopAllConsumers(self, request, context):
        for keys in self.consumers.keys(): self.consumers[keys] = False

    def consumer(self, request, context):
        topicName = request.topicName
        groupName = request.group
        limit = request.limit
        offsetMethod = request.offsetMethod

        if topicName is None or topicName != "": assert "Topic adı boş olamaz."

        self.consumers[topicName] = True
        CONSUMER_GENERATOR = self.kafkaConsumerManager.consumer(topics=[topicName], consumerGroup=groupName, offsetMethod=offsetMethod, limit=limit)
        for msg in CONSUMER_GENERATOR:
            if not context.is_active() or not self.consumers[topicName]:
                CONSUMER_GENERATOR.stopGen()
                self.__removeConsumer(topicName)
                context.set_code(grpc.StatusCode.CANCELLED)
                context.set_details('RPC Client Sonlandırıldığı için server-side consumer sonlandırıldı.')
                logging.warning("RPC Client Sonlandırıldığı için server-side sonlandırılıyor...")
                return rc.ConsumerResponse()
            yield rc.ConsumerResponse(data=msg.value())
        self.__removeConsumer(topicName)
        logging.info(f"{topicName} adlı topic için grup adı: {groupName} olan consumer tamamlandı.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaConsumerServicer_to_server(CKConsumer(), server)
    server.add_insecure_port('[::]:50032')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)
    serve()