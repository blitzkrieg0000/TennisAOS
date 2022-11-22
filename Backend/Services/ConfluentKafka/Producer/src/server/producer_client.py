from __future__ import print_function
import pickle
import queue
import grpc
import kafkaProducer_pb2 as rc
import kafkaProducer_pb2_grpc as rc_grpc

class KafkaProducerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('producerservice:50031') #producerservice:50031
        self.stub = rc_grpc.kafkaProducerStub(self.channel)


    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)
        

    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)


    def producer(self, topicName="test", source="", isVideo=False, limit=-1, errorLimit=3, independent=True):
        # Bir sentinel-generator ile mesaj queuda olana kadar gönderimi bekletiyoruz.
        # Bu yöntem ile Stream-Stream iletişimlerde, döngüler ile iteratorlardan kurtularak "next" ile daha bağımsız kodlama yapabiliyoruz.
        send_queue = queue.SimpleQueue()
        def gen(send_queue):
            while True:
                item = send_queue.get(block=True)
                if item is None:
                    break
                yield item
        responseIterator = self.stub.producer(gen(send_queue))
        send_queue.put(rc.ProducerRequest(TopicName=topicName, Source=source, IsVideo=isVideo, Limit=limit, ErrorLimit=errorLimit, Independent=independent))
        empty_message = rc.ProducerRequest()
        return send_queue, empty_message, responseIterator


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
