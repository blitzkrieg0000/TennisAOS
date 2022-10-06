
import logging
import multiprocessing
import time

import multiprocessing

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

print("Kodlar...")

def islem():
    print("İslem Başladı")
    time.sleep(3)
    print("İslem Tamamlandı")


class KafkaConnect():

    @staticmethod
    def getTopicList():
        topicList = []
        try:
            adminC = AdminClient({'bootstrap.servers': ",".join(["localhost:9092"])})
            topicList = adminC.list_topics().topics.keys()
        except Exception as e: logging.warning(e)
        return topicList

class Repository():
    def __init__(self) -> None:
        self.counter = 0
        self.p = None
        self.adminC = AdminClient({'bootstrap.servers': ",".join(["localhost:9092"])})
        self.SHARED = multiprocessing.Manager().dict()
        self.SHARED["counter"] = 0

    def islem(self):
        topicList = KafkaConnect.getTopicList()
        print(topicList)

    def process(self):
        
        self.p = multiprocessing.Process(target=self.islem)
        self.p.start()

    def wait(self):
        self.p.join()
        self.p.close()

if "__main__" == __name__:

    # try:
    #     multiprocessing.set_start_method("spawn")
    # except: pass

    method = multiprocessing.get_start_method()
    print(method)

    print("Main")
    r = Repository()

    r.process()
    r.wait()