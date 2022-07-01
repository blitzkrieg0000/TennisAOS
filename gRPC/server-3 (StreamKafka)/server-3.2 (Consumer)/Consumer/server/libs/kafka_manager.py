import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
from libs import consts
from confluent_kafka import Consumer
import numpy as np
import cv2

class ConsumerGen():
    def __init__(self, consumerGroup, offsetMethod, topics, limit):
        self.consumer = self.connectKafkaConsumer(consumerGroup, offsetMethod, topics)
        self.consumer.subscribe(topics)
        
        #FLAG && COUNTERS
        self.stopFlag = False
        self.limit = limit
        self.limit_count = 0
        self.ret_limit = 0

    def connectKafkaConsumer(self, consumerGroup, offsetMethod, topics):
        return Consumer({
                'bootstrap.servers': ",".join(consts.KAFKA_BOOTSTRAP_SERVERS),
                'group.id': f"{consumerGroup}-{topics}",
                'auto.offset.reset': offsetMethod
            })

    def closeConnection(self):
        try:
            self.consumer.close()
        except Exception as e:
            logging.warning(f"ConsumerGen: {e}")

    def stopGen(self):
        self.stopFlag = True

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if (self.limit!=-1 and self.limit_count==self.limit) or (self.ret_limit>10) or self.stopFlag:
                self.closeConnection()
                raise StopIteration

            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                self.ret_limit +=1
                continue

            if msg.error():
                logging.info(f"Consumer-error: {msg.error()}")
                self.ret_limit +=1
                continue
            
            self.ret_limit=0
            if self.limit!=-1:
                self.limit_count = 1 + self.limit_count

            return msg

class KafkaManager():
    
    def __init__(self):
        self.producer_thread_statuses = {}
        self.consumerGenerators = {}

    def bytes2Frame(self, img):
        nparr = np.frombuffer(img, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame

    def stopRunningCosumer(self, topicName):
        self.consumerGenerators[topicName].stopGen()

    def stopAllRunningConsumers(self):
        for gen in self.consumerGenerators.keys():
            try: gen.stopGen()
            except: pass
            
    def getRunningConsumers(self):
        return self.consumerGenerators.keys()
    
    def consumer(self, topics=[], consumerGroup="consumergroup-1", offsetMethod="earliest", limit=-1):
        if not topics:
            raise ValueError("topic cannot be empty")
        
        self.consumerGenerators[topics[0]] = ConsumerGen(consumerGroup, offsetMethod, topics, limit)

        for msg in self.consumerGenerators[topics[0]]:
            yield msg.value()

        try: self.consumerGenerators.pop(topics[0])
        except: pass
        