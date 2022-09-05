import logging
import multiprocessing
import os
import signal
import sys
import time

import cv2
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic


class ProducerContextManager():
    def __init__(self, topicName, streamUrl, limit=None):
        self.topicName = topicName
        self.streamUrl = streamUrl
        self.limit = limit
        self._sigint = None
        self._sigterm = None
        self.adminConfluent = None

    def _handler(self, signum, frame):
        logging.warning("Received SIGINT or SIGTERM! Finishing producer, then exiting.")
        #! CLOSE CONNECTION
        sys.exit(0)

    def __enter__(self):
        self._sigint = signal.signal(signal.SIGINT, self._handler)
        self._sigterm = signal.signal(signal.SIGTERM, self._handler)
        self.adminConfluent = AdminClient({'bootstrap.servers': ",".join(["localhost:9092"])})
        return self
     
    def __exit__(self, exc_type, exc_value, exc_traceback):
        signal.signal(signal.SIGINT, self._sigint)
        signal.signal(signal.SIGTERM, self._sigterm)
        print('exit method called')

    def producer(self):
        logging.info(f"Producer Deploying For {self.streamUrl}")
        
        # Connect Producer
        producer = None
        try: producer = Producer({'bootstrap.servers': ",".join(self.KAFKA_BOOTSTRAP_SERVERS)})
        except Exception as e: logging.warning(e)
        if producer is None: assert "Producera bağlanamıyor..."
        
        # Stream Settings
        cam = cv2.VideoCapture(self.streamUrl if os.access(self.streamUrl, mode=0) else self.streamUrl)
        fps = int(cam.get(5))

        cam.set(cv2.CAP_PROP_FRAME_WIDTH, int(cam.get(3)))
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, int(cam.get(4)))
        cam.set(cv2.CAP_PROP_EXPOSURE, 0.1)
        cam.set(cv2.CAP_PROP_FPS, fps if fps>0 else 30)
        cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H265'))
        
        # Create Topic if not exist
        self.KafkaConnect.updateTopics(self.topicName)

        ret_limit_count=0
        limit_count=0
        while self.producer_process_statuses:
            if (limit_count>=self.limit and self.limit > 0) or ret_limit_count>self.RET_COUNT-1:
                break

            ret_val, img = cam.read()
            if ret_val:
                encodedImg = []
                res, encodedImg = cv2.imencode('.png', img)
                if res:
                    producer.produce(self.topicName, encodedImg.tobytes(), callback=self.delivery_report)
                    producer.poll(0)
                    ret_limit_count=0
                    if self.limit > 0:
                        limit_count+=1
                else:
                    logging.info(f"PNG formatına dönüştürülemedi:{self.streamUrl}")
                    ret_limit_count+=1
            else:
                logging.warning(f"{self.topicName}: Streamden okunamıyor... Bu kaynak başka bir yerden kullanımda olabilir: {self.streamUrl}")
                ret_limit_count+=1
        
        # Release Sources
        cam.release()
        producer.flush()

        logging.info(f"Producer Sonlandı: {self.topicName} - RET_LIMIT: {ret_limit_count}/{self.RET_COUNT}")


def streamProducer(topicName, streamUrl, limit=None):
    with ProducerContextManager(topicName, streamUrl, limit=None) as manager:
        print('with statement block')
        #TODO PROCESS


p = multiprocessing.Process(target=streamProducer)
p.start()  

time.sleep(3)
p.terminate()

print("exit")
