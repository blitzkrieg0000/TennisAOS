from __future__ import annotations

import logging
import threading
import time

from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Repositories
from WorkManager import WorkManager

INTERVAL = 3
class ProcessManager():
    
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.workManager = WorkManager()
        self.processList = {}
        self.threadList = []
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
            processData: list = self.checkDatabase()
            for process in processData:

                if len(self.threadList)>self.ConcurencyLimit:
                    continue

                if (process["process_id"] not in self.processList.keys()) and (process["process_id"] not in [item.name for item in self.threadList]):
                    logging.info(f'{process["process_id"]} numaralı process işleme alındı.')
                    self.processList[process["process_id"]] = process
                    data, send_queue, empty_message, responseIterator = self.workManager.Prepare(process, independent=True, errorLimit=3)
                    t = threading.Thread(name=process["process_id"], target=self.workManager.ProducerController, args=(data,))
                    t.start()
                    self.threadList.append(t)

            for thread in self.threadList:
                if not thread.is_alive():
                    Repositories.markAsCompleted(self.rcm, process["process_id"])
                    [self.processList.pop(item) for item in self.processList if item == thread.name]
                    self.threadList.remove(thread)


if __name__ == "__main__":
    processManager = ProcessManager()
    processManager.process()
