from __future__ import annotations

import logging
import threading
from typing import Any

from libs.helpers import Repositories

from StatusChecker import StatusChecker
from clients.Redis.redis_client import RedisCacheManager
from libs.base import AbstractHandler
from WorkManager import WorkManager


class ProcessManager(AbstractHandler):
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.workManager = WorkManager()
        self.processList = {}
        self.threadList = []


    def process(self, processData):
        for process in processData:
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


    def handle(self, data: Any):
        if data is not None:
            self.process(data)
        return super().handle([])


if __name__ == "__main__":
    statusChecker = StatusChecker()
    processManager = ProcessManager()
    data = statusChecker.set_next(processManager).set_next(statusChecker).handle([])