import logging
import multiprocessing
import os
import pickle
import signal
import sys
import threading

import cv2
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from libs.consts import *
from libs.helpers import EncodeManager


class ProducerContextManager(object):
    def __init__(self, data):
        logging.info(data)
        self.topicName = data["topicName"]
        self.streamUrl = data["streamUrl"]
        self.is_video =  data["is_video"]
        self.limit = data["limit"]
        self.adminConfluent = None
        self._sigint = None
        self._sigterm = None
        self.stop_flag = True
        self.cam = None
        self.producerClient = None

    def delivery_report(self, err, msg):
        # Called once for each message produced to indicate delivery result. Triggered by poll() or flush(). 
        if err is not None:
            logging.warning(f'Message delivery failed: {err}')
        else:
        #   logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
            pass

    def getTopicList(self):
        topicList = []
        try: topicList = self.adminConfluent.list_topics().topics.keys()
        except Exception as e: logging.warning(e)
        return topicList

    def createTopics(self, topic_list):
        create_topic_recipies = []
        for new_topic in topic_list:
            created_top = NewTopic(new_topic, num_partitions=TOPICS_NUM_PARTITION, replication_factor=-1)
            create_topic_recipies.append(created_top)
        
        if len(create_topic_recipies)>0:
            fs = None
            try: fs = self.adminConfluent.create_topics(create_topic_recipies)
            except Exception as e: logging.warning(e)
            
            if fs is not None:
                for topic, f in fs.items():
                    try:
                        x = f.result()
                        logging.info(f"Topic {topic} created")
                    except Exception as e:
                        logging.warning(f"Failed to create topic {topic}: {e}") 

    def updateTopics(self, topicName):
        topics = set(self.getTopicList())
        existTopics = topics - TOPICS_IGNORE_SET
        newTopicName = set([topicName])
        self.createTopics((newTopicName - existTopics))

    def _handler(self, signum, frame):
        logging.warning("Received SIGINT or SIGTERM! Finishing self.producerClient, then exiting.")
        #! CLOSE CONNECTION
        # Release Sources
        self.cam.release()
        self.producerClient.flush()
        sys.exit(0)

    def __enter__(self):
        self._sigint = signal.signal(signal.SIGINT, self._handler)
        self._sigterm = signal.signal(signal.SIGTERM, self._handler)
        self.adminConfluent = AdminClient({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        try: self.producerClient = Producer({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        except Exception as e: logging.warning(e)
        if self.producerClient is None: assert "Producera bağlanamıyor..."
        return self
     
    def __exit__(self, exc_type, exc_value, exc_traceback):
        signal.signal(signal.SIGINT, self._sigint)
        signal.signal(signal.SIGTERM, self._sigterm)
        logging.warning('Exit Producer')
    
    def producer(self):
        logging.info(f"Producer Deploying For {self.streamUrl}, TopicName: {self.topicName}")
        
        # Stream Settings
        if self.is_video and not os.access(self.streamUrl, mode=0):
            raise "Video Kaynakta Bulunamadı. Dosya Yolunu Kontrol Ediniz..."

        self.cam = cv2.VideoCapture(self.streamUrl)
        fps = int(self.cam.get(5))

        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.cam.get(3)))
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.cam.get(4)))
        self.cam.set(cv2.CAP_PROP_EXPOSURE, 0.1)
        self.cam.set(cv2.CAP_PROP_FPS, fps if fps>0 else 30)
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H265'))
        
        # Create Topic if not exist
        self.updateTopics(self.topicName)

        ret_limit_count=0
        limit_count=0
        while self.stop_flag:
            if (limit_count>=self.limit and self.limit > 0) or ret_limit_count>RET_COUNT-1:
                break

            ret_val, img = self.cam.read()
            if ret_val:
                encodedImg = []

                res, encodedImg = cv2.imencode('.jpg', img) #.png formatından boyutu daha düşük
                if res:
                    self.producerClient.produce(self.topicName, encodedImg.tobytes(), callback=self.delivery_report)
                    self.producerClient.poll(0)
                    ret_limit_count=0
                    if self.limit > 0:
                        limit_count+=1
                else:
                    logging.info(f"PNG formatına dönüştürülemedi:{self.streamUrl}")
                    ret_limit_count+=1
            else:
                logging.warning(f"{self.topicName}: Streamden okunamıyor...Kaynak kullanımda olabilir: {self.streamUrl}")
                ret_limit_count+=1
        
        logging.info(f"Producer Sonlandı: {self.topicName} - RET_LIMIT: {ret_limit_count}/{RET_COUNT}")


class KafkaProducerManager():

    def __init__(self):
        self.adminC = AdminClient({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        self.kcm = KafkaConsumerManager()
        self.producer_process_statuses = {} # multiprocessing.Manager().dict()
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def delivery_report(self, err, msg):
        # Called once for each message produced to indicate delivery result. Triggered by poll() or flush(). 
        if err is not None:
            logging.warning(f'Message delivery failed: {err}')
        else:
        #   logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
            pass

    def getTopicList(self):
        topicList = self.adminC.list_topics().topics.keys()
        return topicList

    def deleteTopics(self, topic_list):
        if len(topic_list) > 0:
            fs = self.adminC.delete_topics(topic_list)
            for topic, f in fs.items():
                try:
                    x = f.result()
                    logging.info(f"Topic {topic} deleted")
                except Exception as e:
                    logging.warning(f"Failed to delete topic {topic}: {e}")

    def deleteNotUsingTopic(self):
        topics = set(self.getTopicList())
        existTopics = topics - TOPICS_IGNORE_SET

        producer_items = set(self.producer_process_statuses.keys())
        producerDellTopics = existTopics - producer_items

        consumer_items = set(self.bytes2obj(self.kcm.getRunningConsumers()))
        dellTopics = producerDellTopics - consumer_items

        self.deleteTopics([*dellTopics])

    def updateThreads(self): 
        # Eğer bu thread yoksa temizle
        running_threads = [thread.name for thread in threading.enumerate()]
        items = list(self.producer_process_statuses.keys())
        for item in items:
            if not item in running_threads:
                try:
                    self.producer_process_statuses.pop(item)
                except: pass
   
    def getProducerThreads(self):
        self.updateThreads()
        self.deleteNotUsingTopic()
        return self.producer_process_statuses

    def stopProducerThread(self, thread_name):
        logging.info(f"THREAD: {thread_name} varsa durdurulmaya çalışılacak.")
        if thread_name in [thread.name for thread in threading.enumerate()]:
            try:
                self.producer_process_statuses[thread_name] = False
            except: pass

        self.updateThreads()

    def stopAllProducerThreads(self):
        items = list(self.producer_process_statuses.keys())
        for x in items:
            try:
                self.producer_process_statuses[x] = False
            except: pass
        self.updateThreads()

    def producers(func):
        def wrapper(self, *args, **kwargs):
            data = args[0]
            
            if data["topicName"] is None or data["topicName"] == "":
                raise ValueError("topicName cannot be empty.")
            
            if data["limit"] is None or data["limit"] == "":
                data["limit"] = -1

            t = multiprocessing.Process(name=data["topicName"], target=func, args=(self, *args), kwargs=kwargs)
            t.start()

            return data["topicName"]
        return wrapper

    @producers
    def streamProducer(self, data):
        with ProducerContextManager(data) as manager:
            manager.producer()


