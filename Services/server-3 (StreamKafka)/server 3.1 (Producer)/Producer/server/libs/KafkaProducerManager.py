import logging
import multiprocessing
import os
import signal
import sys
from multiprocessing.process import BaseProcess
import time

import cv2
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from libs.consts import *
from libs.helpers import Converters
from libs.Response import Response, ResponseCodes


class ProducerContextManager(object):
    def __init__(self, data):
        logging.info(data)
        self.topicName = data["topicName"]
        self.streamUrl = data["source"]
        self.is_video =  data["is_video"]
        self.limit = data["limit"]
        self.adminConfluent = None
        self._sigint = None
        self._sigterm = None
        self.stop_flag = True
        self.cam = None
        self.producerClient = None

    def __delivery_report(self, err, msg):
        # Called once for each message produced to indicate delivery result. Triggered by poll() or flush(). 
        if err is not None:
            logging.warning(f'Message delivery failed: {err}')
        else:
        #   logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
            pass

    def __deleteAllTopics(self):
        topic_list = self.__getTopicList()
        delete_topic_list = []
        [delete_topic_list.append(item) for item in topic_list if item != "__consumer_offsets"]
        if len(delete_topic_list)>0:
            fs = self.adminConfluent.delete_topics(delete_topic_list)
            for topic, f in fs.items():
                try:
                    f.result()
                    print("Topic {} deleted".format(topic))
                except Exception as e:
                    print("Failed to delete topic {}: {}".format(topic, e))

    def __getTopicList(self):
        topicList = []
        try: topicList = self.adminConfluent.list_topics().topics.keys()
        except Exception as e: logging.warning(e)
        return topicList

    def __createTopics(self, topic_list):
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
                        logging.error(f"Failed to create topic {topic}: {e}")

    def __updateTopics(self, topicName):
        topics = set(self.__getTopicList())
        existTopics = topics - TOPICS_IGNORE_SET
        newTopicName = set([topicName])
        self.__createTopics((newTopicName - existTopics))

    def __handler(self, signum, frame):
        logging.warning("Received SIGINT or SIGTERM! Closing Connections, then exiting Producer.")
        self.__closeConnections()
        sys.exit(0)

    def __enter__(self):
        self._sigint = signal.signal(signal.SIGINT, self.__handler)
        self._sigterm = signal.signal(signal.SIGTERM, self.__handler)
        self.adminConfluent = AdminClient({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        try: self.producerClient = Producer({'bootstrap.servers': ",".join(KAFKA_BOOTSTRAP_SERVERS)})
        except Exception as e: logging.warning(e)
        if self.producerClient is None: assert "Producera bağlanamıyor..."
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        signal.signal(signal.SIGINT, self._sigint)
        signal.signal(signal.SIGTERM, self._sigterm)
        self.__closeConnections()
        logging.warning('Normal Exiting Producer')

    def __closeConnections(self):
        self.stop_flag = False
        self.cam.release()
        self.producerClient.flush()

    def producer(self, qq, lock):
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
        #self.__deleteAllTopics()
        self.__updateTopics(self.topicName)

        ret_limit_count=0
        limit_count=0
        while self.stop_flag:
            if (limit_count>=self.limit and self.limit > 0) or not ret_limit_count<=RET_COUNT-1:
                break

            ret_val, img = self.cam.read()
            if ret_val:
                encodedImg = []
                encodedImg = Converters.frame2bytes(img)
                if encodedImg is not None:
                    lock.acquire(block=True)
                    
                    qq["frame"] = encodedImg
                    #qq.put(encodedImg, block=True, timeout=120.0)

                    lock.release()

                    self.producerClient.produce(self.topicName, encodedImg, callback=self.__delivery_report)
                    self.producerClient.poll(0)
                    ret_limit_count=0
                    if self.limit > 0:
                        limit_count+=1
                else:
                    logging.warning(f"Frame to Byte convertion failed:{self.streamUrl}")
                    ret_limit_count+=1
            else:
                logging.warning(f"Topic <{self.topicName}>: Bu kaynak kullanımda olabilir: <{self.streamUrl}>. Streamden okunamıyor. RET_LIMIT: {ret_limit_count}")
                ret_limit_count+=1

        logging.info(f"Producer Sonlandı: <{self.topicName}>. RET_LIMIT: {ret_limit_count}/{RET_COUNT-1}")

class KafkaProducerManager():
    def __init__(self):
        self.producer_process_statuses = {} # multiprocessing.Manager().dict()
        
    def __getAllProceses(self):
        return multiprocessing.active_children()

    def __getProcessByName(self, name):
        for process in self.__getAllProceses():
            if process.name == name: return process
        return None

    def __stopProcess(self, process:BaseProcess):
        try:
            if process.is_alive():
                process.terminate()
                process.join(time=1)
                if process.is_alive():
                    process.kill()
            process.close()
            del process
        except Exception as e:
            logging.warning(e)

    def getAllProducerProcesses(self):
        return Response(ResponseCodes.INFO, "", [process.name for process in self.__getAllProceses() if process.is_alive])

    def stopProducerProcess(self, processName):
        logging.info(f"{processName} isimli process varsa durdurulmaya çalışılacak.")
        process = self.__getProcessByName(processName)
        if process is not None:
            self.__stopProcess(process)
        else:
            return Response(ResponseCodes.NOT_FOUND, "Durdurulacak böyle bir process bulunamadı.")
        return Response(ResponseCodes.SUCCESS, f"{processName} adlı process başarıyla durduruldu." if self.__getProcessByName(processName) is None else f"{processName} durdurulmaya çalışılıyor.")

    def stopAllProducerProcesses(self) -> Response:
        allProcesses = self.__getAllProceses()
        for process in allProcesses:
            self.__stopProcess(process)
        return Response(ResponseCodes.INFO, f"Çalışan tüm processler durdurulacak... Çalışan process sayısı: {len(allProcesses)}")

    def ProducerMultiProcess(func):
        def wrapper(self, *args, **kwargs):

            if args[0]["topicName"] is None or args[0]["topicName"] == "":
                return Response(ResponseCodes.REQUIRED, "Topic adı boş bırakılamaz.")
            
            if args[0]["limit"] is None or args[0]["limit"] == "":
                args[0]["limit"] = -1

            t = multiprocessing.Process(name=args[0]["topicName"], target=func, args=(self, *args), kwargs=kwargs)
            t.start()
            
            return Response(ResponseCodes.SUCCESS, f"Producer Started For: {args[0]['topicName'] }")
        return wrapper

    @ProducerMultiProcess
    def startProducer(self, data, qq, lock) -> Response:
        with ProducerContextManager(data) as manager:
            manager.producer(qq, lock)