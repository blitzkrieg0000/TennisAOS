from __future__ import annotations

import concurrent.futures
from typing import Any

from AlgorithmManager import AlgorithmManager
from clients.Redis.redis_client import RedisCacheManager
from libs.base import AbstractHandler
from StatusChecker import StatusChecker


class ProcessManager(AbstractHandler):
    def __init__(self):
        MAX_WORKERS:int = 5
        self.rcm = RedisCacheManager()
        self.algorithmManager = AlgorithmManager()
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
    sc = StatusChecker()
    results = sc.set_next(ProcessManager()).set_next(sc).handle([])
