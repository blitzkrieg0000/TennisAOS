from __future__ import annotations

import concurrent.futures
import logging
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.base import AbstractHandler
from libs.helpers import Repositories
from WorkManager import WorkManager


class ProcessManager(AbstractHandler):
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.algorithmManager = WorkManager()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.processList = []
        self.futureIterators = []

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
                    Repositories.markAsCompleted(self.rcm, process["process_id"])
                    self.processList.remove(process)
                    data = future.result()
        return processData

    def handle(self, data: Any):
        if data is not None:
            data = self.process(data)
        return data
        # return super().handle(data)
