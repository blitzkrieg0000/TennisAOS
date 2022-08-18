import os
import pickle
import threading
from libs.consts import *

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import cv2
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from libs.logger import logger
class KafkaManager():

    def __init__(self):
        self.adminC = AdminClient({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        self.producer_thread_statuses = {}
        self.kcm = KafkaConsumerManager()

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def delivery_report(self, err, msg):
        # Called once for each message produced to indicate delivery result. Triggered by poll() or flush(). 
        if err is not None:
            logger.warning(f'Message delivery failed: {err}')
        else:
        #   logger.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
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
                    logger.info(f"Topic {topic} created")
                except Exception as e:
                    logger.warning(f"Failed to create topic {topic}: {e}") 

    def deleteTopics(self, topic_list):
        if len(topic_list) > 0:
            fs = self.adminC.delete_topics(topic_list)
            for topic, f in fs.items():
                try:
                    f.result()
                    logger.info(f"Topic {topic} deleted")
                except Exception as e:
                    logger.warning(f"Failed to delete topic {topic}: {e}")

    def updateTopics(self, topicName):
        topics = set(self.getTopicList().topics.keys())
        existTopics = topics - TOPICS_IGNORE_SET
        newTopicName = set([topicName])
        self.createTopics((newTopicName - existTopics))

    def deleteNotUsingTopic(self):
        topics = set(self.getTopicList().topics.keys())
        existTopics = topics - TOPICS_IGNORE_SET

        producer_items = set(self.producer_thread_statuses.keys())
        producerDellTopics = existTopics - producer_items

        consumer_items = set(self.bytes2obj(self.kcm.getRunningConsumers()))
        dellTopics = producerDellTopics - consumer_items

        # TODO: Farkını bul
        self.deleteTopics([*dellTopics])

    def updateThreads(self): 
        # Eğer bu thread yoksa temizle
        running_threads = [thread.name for thread in threading.enumerate()]
        items = list(self.producer_thread_statuses.keys())
        for item in items:
            if not item in running_threads:
                try:
                    self.producer_thread_statuses.pop(item)
                except: pass

        self.deleteNotUsingTopic()


    def getProducerThreads(self):
        self.updateThreads()
        return self.producer_thread_statuses

    def stopProducerThread(self, thread_name):
        logger.info(f"THREAD: {thread_name} varsa durdurulmaya çalışılacak.")
        if thread_name in [thread.name for thread in threading.enumerate()]:
            try:
                self.producer_thread_statuses[thread_name] = False
            except: pass

        self.updateThreads()

    def stopAllProducerThreads(self):
        items = list(self.producer_thread_statuses.keys())
        for x in items:
            try:
                self.producer_thread_statuses[x] = False
            except: pass
        self.updateThreads()

    def producers(func):
        def wrap(self, *args, **kwargs):
            #items = args[0].split("-")   #{prefix}-{id}-{random_id} ->  streaming_thread_tenis_saha_1-0

            thread_name = f"{THREAD_PREFIX}{args[0]}" #f"{THREAD_PREFIX}{items[0]}-{items[1]}"
            if not kwargs.get("thName", False):
                kwargs['thName'] = thread_name

            if not kwargs.get("limit", False):
                kwargs['limit'] = -1

            self.updateThreads()
            self.producer_thread_statuses[kwargs['thName']] = True 
            t = threading.Thread(name=kwargs['thName'], target=func, args=(self, *args), kwargs=kwargs)
            t.start()
            logger.info(f"Starting: {kwargs['thName']}")
        
            return kwargs['thName']
        return wrap

    @producers
    def streamProducer(self, topicName, streamUrl, limit=None, thName=None):
        if not topicName:
            raise ValueError("Topic adı boş bırakılamaz!")

        producer = Producer({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        logger.info(f"Stream-Producer şu kaynak için {topicName}'e {limit if limit!=-1 else 'stream sonuna'} kadar veri yüklüyor: {streamUrl}")

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

        ret_limit_count=0
        limit_count=0
        while self.producer_thread_statuses[thName]:
            if (limit_count>=limit and limit > 0) or ret_limit_count>RET_COUNT-1:
                break

            ret_val, img = cam.read()
            if ret_val:

                encodedImg = []
                res, encodedImg = cv2.imencode('.jpg', img)
                if res:
                    producer.produce(topicName, encodedImg.tobytes(), callback=self.delivery_report)
                    producer.poll(0)
                    ret_limit_count=0
                    if limit > 0:
                        limit_count+=1
                else:
                    logger.info(f"Streamdeki resim karesi jpg formatına dönüştürülemedi:{streamUrl}")
                    ret_limit_count+=1
            else:
                logger.info(f"WARNING {thName}: Streamden okunamıyor... Bu kaynak başka bir yerden kullanımda olabilir: {streamUrl}")
                ret_limit_count+=1
        
        # Release Sources
        cam.release()
        producer.flush()
        
        self.updateThreads()
        logger.info(f"Producer Sonlandı: {thName} - RET_LIMIT: {ret_limit_count}/{RET_COUNT}")
        