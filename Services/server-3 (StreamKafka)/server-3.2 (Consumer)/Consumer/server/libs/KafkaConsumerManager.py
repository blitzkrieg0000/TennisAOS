import logging
import time

from confluent_kafka import Consumer

from libs.consts import *


class ConsumerGen():
    def __init__(self, topics, consumerGroup, offsetMethod, limit):
        self.consumer = self.connectKafkaConsumer(consumerGroup, offsetMethod, topics)
        self.subscribe(topics)
        
        #FLAG && COUNTERS
        self.stopFlag = False
        self.limit = limit
        self.limit_count = 0
        self.ret_limit = 0
    
    def subscribe(self, topics, try_count=3):
        counter=0
        while True:
            try:
                self.consumer.subscribe(topics)
                break
            except:
                logging.error("Topic'e bağlanılamıyor.")
                time.sleep(1)
                counter += 1
                if counter > try_count:
                    raise ConnectionError("Topic'e bağlanılamıyor.")

    def connectKafkaConsumer(self, consumerGroup, offsetMethod, topics):
        # fetch.message.max.bytes : ""
        #"message.max.bytes": 20971520
        return Consumer({
                'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS),
                'group.id': consumerGroup,
                'auto.offset.reset': offsetMethod,
                'fetch.message.max.bytes' : 20971520,
                "message.max.bytes": 20971520
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
        if (self.limit!=-1 and self.limit_count==self.limit) or (self.ret_limit>50) or self.stopFlag:
            self.closeConnection()
            raise StopIteration

        msg = self.consumer.poll(0)
        logging.warning(str(msg))
        if msg is None:
            self.ret_limit = 1 + self.ret_limit
            if self.ret_limit > 10: 
                time.sleep(1)
            return None

        if msg.error():
            logging.warning(str(msg.error()))
            self.ret_limit = 1 + self.ret_limit
            if self.ret_limit > 10: 
                time.sleep(1)
            return None

        self.ret_limit=0
        if self.limit!=-1:
            self.limit_count = 1 + self.limit_count
        
        return msg


class KafkaConsumerManager():
    def __init__(self):
        self.consumerGenerators = {}

    def stopRunningCosumer(self, topicName):
        try: self.consumerGenerators[topicName].stopGen()
        except KeyError as e: print(e)

    def stopAllRunningConsumers(self):
        for gen in self.consumerGenerators.keys():
            try: gen.stopGen()
            except: pass
            
    def getRunningConsumers(self):
        return list(self.consumerGenerators.keys())
    
    def consumer(self, topics=[], consumerGroup="consumergroup-1", offsetMethod="earliest", limit=-1):
        if not topics or len(topics)<0: 
            raise ValueError("topic cannot be empty")
        return ConsumerGen(topics, consumerGroup, offsetMethod, limit)
