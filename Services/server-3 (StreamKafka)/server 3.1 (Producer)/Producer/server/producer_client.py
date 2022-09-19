from __future__ import print_function
import pickle
import queue
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
        send_queue = queue.SimpleQueue()
        responseIterator = self.stub.producer(iter(send_queue.get, None))
        responseIterator = self.stub.producer(requestData)
        send_queue.put(requestData)
        emptyRequest = rc.producerRequest(data="")
        return send_queue, emptyRequest, responseIterator

    def getAllProducerProcesses(self):
        requestData = rc.getAllProducerProcessesRequest(data="")
        responseData = self.stub.getAllProducerProcesses(requestData)
        return responseData.data

    def stopAllProducerProcesses(self):
        requestData=rc.stopAllProducerProcessesRequest(data="")
        responseData = self.stub.stopAllProducerProcesses(requestData)
        return responseData.result

    def stopProducer(self, process_name):        
        requestData = rc.stopProducerRequest(process_name=process_name)
        responseData = self.stub.stopProducer(requestData)
        return responseData.result
    
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
