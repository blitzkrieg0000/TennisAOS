from concurrent import futures
import pickle

import grpc
import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc
from libs.kafka_manager import KafkaManager

import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
class CKProducer(rc_grpc.kafkaProducerServicer):
    def __init__(self):
        super().__init__()
        self.kafkaManager = KafkaManager()

    def obj2bytes(self, obj):
        return pickle.dumps(obj)
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def producer(self, request, context):
        topicName = request.topicName
        streamUrl = request.streamUrl
        limit = request.limit
        thread_name = self.kafkaManager.streamProducer(topicName, streamUrl, limit=limit)
        responseData = rc.producerResponse(result=f"Producer Mesajı Aldı: {topicName} - {streamUrl}", thread_name=thread_name)
        return responseData

    def getProducerThreads(self, request, context):
        th = self.obj2bytes(self.kafkaManager.producer_thread_statuses)
        return rc.getProducerThreadsResponse(data=th)

    def stopAllProducerThreads(self, request, context):
        self.kafkaManager.stopAllProducerThreads()
        responseData = rc.stopAllProducerThreadsResponse(data=f"Tüm Producer Thread ler Durdurulmaya Çalışılıyor...")
        return responseData

    def stopProduce(self, request, context):
        thread_name = request.thread_name
        self.kafkaManager.stopProducerThread(thread_name)
        responseData = rc.stopProduceResponse(result=f"Durdurulmaya Çalışılacak Stream Thread: {thread_name}")
        return responseData

    def deleteTopics(self, request, context):
        requestData = self.bytes2obj(request.data)
        self.kafkaManager.deleteTopics(requestData)
        return rc.deleteTopicsResponse(data=f"Deleting Topics: {requestData}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_kafkaProducerServicer_to_server(CKProducer(), server)
    server.add_insecure_port('[::]:50031')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()