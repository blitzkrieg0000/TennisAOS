from __future__ import annotations

import logging
import threading
import time

from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Repositories
from WorkManager import WorkManager

INTERVAL = 5
class ProcessManager():
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.workManager = WorkManager()
        self.ConcurencyLimit = 1

    def timer(func):
        def wrapper(self, *args, **kwargs):
            time.sleep(INTERVAL)
            return func(self, *args,  **kwargs)
        return wrapper


    @timer
    def checkDatabase(self):
        return Repositories.getAllProcessRelated(self.rcm)


    def process(self):
        while True:
            processes: list = self.checkDatabase()

            if len(processes)==0:
                continue
            
            threadList:list[threading.Thread] = []
            for i, process in enumerate(processes):
                
                if i>=self.ConcurencyLimit:
                    break
                logging.info(f"{process['process_id']} işleme alındı.")
                data, send_queue, empty_message, responseIterator = self.workManager.Prepare(process, independent=True, errorLimit=3)
                t = threading.Thread(name=process["process_id"], target=self.workManager.ProducerController, args=(data,))
                threadList.append(t)
            
            for thread in threadList:
                thread.start()

            for thread in threadList:
                thread.join()
            
            del threadList



if __name__ == "__main__":
    processManager = ProcessManager()
    processManager.process()
