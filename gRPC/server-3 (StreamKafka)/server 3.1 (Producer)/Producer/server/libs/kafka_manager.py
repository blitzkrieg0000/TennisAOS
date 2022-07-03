import os
import threading
from libs.consts import *

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import cv2

import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)

class KafkaManager():

    def __init__(self):
        self.adminC = AdminClient({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        self.producer_thread_statuses = {}
        self.producer_threads = {}
        self.limit_count = {}

    def delivery_report(self, err, msg):
        # Called once for each message produced to indicate delivery result. Triggered by poll() or flush(). 
        if err is not None:
            logging.warning(f'Message delivery failed: {err}')
        else:
        #   logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
            pass

    def getTopicList(self):
        topicList = self.adminC.list_topics() #.topics.keys()
        return topicList

    def createTopics(self, topic_list):
        create_topic_recipies = []
        for new_topic in topic_list:
            created_top = NewTopic(new_topic, num_partitions=TOPICS_NUM_PARTITION, replication_factor=-1)
            create_topic_recipies.append(created_top)

        if len(create_topic_recipies)>0:
            fs = self.adminC.create_topics(create_topic_recipies)
            for topic, f in fs.items():
                try:
                    f.result()
                    logging.info(f"Topic {topic} created")
                except Exception as e:
                    logging.warning(f"Failed to create topic {topic}: {e}") 

    def deleteTopics(self, topic_list):
        delete_topic_recipies = []
        for delete_topic in topic_list:
            delete_topic_recipies.append(delete_topic)
        if delete_topic_recipies:
            fs = self.adminC.delete_topics(delete_topic_recipies)
            for topic, f in fs.items():
                try:
                    f.result()
                    logging.info(f"Topic {topic} deleted")
                except Exception as e:
                    logging.warning(f"Failed to delete topic {topic}: {e}")

    def updateTopics(self, topicName):
        topics = set(self.getTopicList().topics.keys())
        existTopics = topics - TOPICS_IGNORE_SET
        newTopicName = set([topicName])
        self.createTopics((newTopicName - existTopics))

    def updateThreads(self):
        # Eğer bu thread yoksa temizle
        running_threads = [thread.name for thread in threading.enumerate()]
        items = list(self.producer_thread_statuses.keys())
        for item in items:
            if not item in running_threads:
                try:
                    self.producer_thread_statuses.pop(item)
                    self.producer_threads.pop(item)
                except: pass

    def getProducerThreads(self):
        self.updateThreads()
        return self.producer_thread_statuses

    def stopProducerThread(self, thread_name):
        logging.info(f"THREAD: {thread_name} varsa durdurulmaya çalışılacak.")
        if thread_name in [thread.name for thread in threading.enumerate()] and thread_name in self.producer_threads:
            if self.producer_threads[thread_name].is_alive():
                self.producer_thread_statuses[thread_name] = False
        self.updateThreads()

    def stopAllProducerThreads(self):
        items = list(self.producer_thread_statuses.keys())
        for x in items:
            self.producer_thread_statuses[x] = False
        self.updateThreads()
        
    def producers(func):
        def wrap(self, *args, **kwargs):
            items = args[0].split("-")   #{prefix}-{id}-{random_id} ->  streaming_thread_tenis_saha_1-0

            thread_name = f"{THREAD_PREFIX}{items[0]}-{items[1]}"
            if not kwargs.get("thName", False):
                kwargs['thName'] = thread_name

            if not kwargs.get("limit", False):
                kwargs['limit'] = -1

            _ = self.getProducerThreads() # Updata
            self.stopProducerThread(kwargs['thName'])

            t = threading.Thread(name=kwargs['thName'], target=func, args=(self, *args), kwargs=kwargs)
            t.start()
            
            logging.info(f"Starting: {kwargs['thName']}, Alive-Status: {t.is_alive()}")
            self.producer_thread_statuses[kwargs['thName']] = True  
            self.producer_threads[kwargs['thName']] = t
            return kwargs['thName']
        return wrap

    @producers
    def streamProducer(self, topicName, streamUrl, limit=None, thName=None):
        if not topicName:
            raise ValueError("Topic adı boş bırakılamaz!")

        producer = Producer({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        logging.info(f"Stream-Producer şu kaynak için {topicName}'e {limit if limit!=-1 else 'stream sonuna'} kadar veri yüklüyor: {streamUrl}")

        # Stream ayarları
        cam = cv2.VideoCapture(f"/assets/{streamUrl}" if os.access(f"/assets/{streamUrl}", mode=0) else streamUrl)
        fps = int(cam.get(5))

        cam.set(cv2.CAP_PROP_FRAME_WIDTH, int(cam.get(3)))
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, int(cam.get(4)))
        cam.set(cv2.CAP_PROP_EXPOSURE, 0.1)
        cam.set(cv2.CAP_PROP_FPS, fps if fps>0 else 30)
        cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H265'))
        
        # Topic yoksa oluştur
        self.updateTopics(topicName)

        ret_limit=0
        self.limit_count[thName]=0
        while self.producer_thread_statuses[thName]:
            if (self.limit_count[thName]>=limit and limit != -1) or ret_limit>10:
                break

            ret_val, img = cam.read()
            if ret_val:

                encodedImg = []
                res, encodedImg = cv2.imencode('.jpg', img)
                if res:
                    producer.produce(topicName, encodedImg.tobytes(), callback=self.delivery_report)
                    producer.poll(0)
                    ret_limit=0
                    if limit != -1:
                        self.limit_count[thName]+=1
                else:
                    logging.info(f"Streamdeki resim karesi jpg formatına dönüştürülemedi:{streamUrl}")
                    ret_limit+=1
            else:
                logging.info(f"WARNING {thName}: Streamden okunamıyor... val:{ret_val}, url:{streamUrl}")
                ret_limit+=1
        
        #RELEASE SOURCES
        cam.release()
        producer.flush()

        # Produce işlemi sonlanacak olsa da garantilemek için
        self.limit_count[thName]=0
        try:
            self.limit_count.pop(thName)
        except KeyError as e:
            logging.warning(e)
        finally:
            logging.info(f"Finish: {thName} - RET_LIMIT: {ret_limit}/10")
        self.updateThreads()