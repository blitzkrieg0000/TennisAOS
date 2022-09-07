from concurrent import futures

import grpc
import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc
from libs.KafkaConsumerManager import KafkaConsumerManager
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
        for i, msg in enumerate(CONSUMER_GENERATOR):
            logging.warning(i)
            if not context.is_active():
                CONSUMER_GENERATOR.stopGen()
                context.set_code(grpc.StatusCode.CANCELLED)
                context.set_details('RPC Client Sonlandırıldığı için server-side consumer sonlandırıldı.')
                logging.warning("RPC Client Sonlandırıldığı için server-side sonlandırılıyor...")
                return rc.ConsumerResponse()
            yield rc.ConsumerResponse(data=msg.value())
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