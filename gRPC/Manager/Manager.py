from __future__ import annotations

import time
from typing import Any
import pickle
import concurrent.futures
from clients.Redis.redis_client import RedisCacheManager
from AlgorithmManager import AlgorithmManager
from libs.base import AbstractHandler


INTERVAL = 3 # Second(s)

def bytes2obj(bytes):
    if bytes is not None or bytes != b'':
        return pickle.loads(bytes)

def timer(func):
    def wrapper(*args, **kwargs):
        time.sleep(INTERVAL)
        return func(*args,  **kwargs)
    return wrapper


class StatusChecker(AbstractHandler):
    def __init__(self) -> None:
        self.rcm = RedisCacheManager()

    @timer
    def checkDatabase(self):
        query_keys = ["process_id", "process_name", "session_id", "stream_id", "aos_type_id", "player_id", "court_id", "limit", "force"]
        QUERY = f'''SELECT p.id, p.name, s.id, s.stream_id, s.aos_type_id, s.player_id, s.court_id, s."limit", s."force" FROM public."Process" as p INNER JOIN public."SessionParameter" as s ON p.session_id = s.id WHERE p.is_completed=false'''
        processData = self.rcm.Read(query=QUERY, force = True)
        
        processes = bytes2obj(processData)
        
        processData = []
        for process in processes:
            process_dict = {}
            for i, key in enumerate(query_keys):
                process_dict[key] = process[i]
            processData.append(process_dict)
        
        return processData
    
    def handle(self, data: Any):
        data: list = self.checkDatabase()
        return super().handle(data)


class ProcessManager(AbstractHandler):
    def __init__(self):
        self.rcm = RedisCacheManager()
        self.algorithmManager = AlgorithmManager()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.processList = []
        self.futureIterators = []

    def markAsCompleted(self, process):
        self.rcm.writeCache(f'UPDATE public."Process" SET is_completed=%s WHERE id={process["process_id"]};', [True,])

    def process(self, processData):

        for process in processData:
            if process not in self.processList:
                self.processList.append(process)

        if len(self.processList) > 0:
            threadSubmits = {self.executor.submit(self.algorithmManager.StartGameObservationController, process) : process for process in self.processList}
            futureIterator = concurrent.futures.as_completed(threadSubmits)
            self.futureIterators.append(futureIterator)
        

        for futureIterator in self.futureIterators:
            for future in futureIterator:
                if future.done():
                    process = threadSubmits[future]
                    #self.markAsCompleted(process)
                    print("Marked As Completed")
                    self.processList.remove(process)

        return processData

    def handle(self, data: Any):
        data: dict = self.process(data)
        return super().handle(data)


if __name__ == "__main__":

    sc = StatusChecker()
    results = sc.set_next(ProcessManager()).set_next(sc).handle({})
