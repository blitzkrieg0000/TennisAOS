from __future__ import annotations

import concurrent.futures
import logging
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.base import AbstractHandler
from StatusChecker import StatusChecker
from WorkManager import WorkManager


def logo():
    f = open("Services/server-1 (MainServer)/MainServer/server/libs/logo.txt", "r")
    logo = f.read()
    f.close()
    print(logo, "\n")

class ProcessManager(AbstractHandler):
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.algorithmManager = WorkManager()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.processList = []
        self.futureIterators = []

    def markAsCompleted(self, process):
        self.rcm.Write(f'UPDATE public."Process" SET is_completed=%s WHERE id={process["process_id"]};', [True,])

    def process(self, processData):
        for process in processData:
            if process not in self.processList:
                self.processList.append(process)

        if len(self.processList) > 0:
            [logging.info(f'{process["process_id"]} numaralı process işleme alındı.') for process in self.processList]
            threadSubmits = {self.executor.submit(self.algorithmManager.StartGameObservationController, process) : process for process in self.processList}
            futureIterator = concurrent.futures.as_completed(threadSubmits)

            for future in futureIterator:
                if future.done():
                    process = threadSubmits[future]
                    self.markAsCompleted(process)
                    self.processList.remove(process)
                    data = future.result()
        return processData

    def handle(self, data: Any):
        if data is not None:
            data = self.process(data)
        return super().handle(data)


if __name__ == "__main__":
    logo()
    statusChecker = StatusChecker()
    processManager = ProcessManager()

    statusChecker.set_next(processManager)
    processManager.set_next(statusChecker)

    statusChecker.handle([])