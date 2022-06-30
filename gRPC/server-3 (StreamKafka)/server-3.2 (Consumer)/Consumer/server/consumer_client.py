from __future__ import print_function
import logging
import grpc
import kafkaConsumer_pb2 as rc
import kafkaConsumer_pb2_grpc as rc_grpc
import numpy as np
import cv2
class KafkaConsumerManager():
    def __init__(self):
        self.channel = grpc.insecure_channel('consumerservicepool.default.svc.cluster.local:50032')
        self.stub = rc_grpc.kafkaConsumerStub(self.channel)

    def bytes2frame(self, byte_img ):
        nparr = np.frombuffer(byte_img, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
        return frame

    def consumer(self, topicName, groupName, limit=-1, show=True):
        requestData = rc.ConsumerRequest(topicName=topicName, group=groupName, limit=limit)
        CONSUMER_GENERATOR = self.stub.consumer(requestData)

        for res in CONSUMER_GENERATOR:
            if res.data is b"None":
                return None

            if show:
                cv2.imshow(str(groupName), self.bytes2frame(res.data))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            logging.info("Consumer: ?")
            yield res.data

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