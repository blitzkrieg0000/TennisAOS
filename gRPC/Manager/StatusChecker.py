from __future__ import annotations

import pickle
import time
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.base import AbstractHandler
from libs.logger import logger


INTERVAL = 3 # Second(s)

def bytes2obj(bytes):
    if bytes is not None or bytes != b'':
        return pickle.loads(bytes)

def timer(func):
    def wrapper(*args, **kwargs):
        time.sleep(INTERVAL)
        
        logger.info("Yeni Processler Kontrol Ediliyor...")
        return func(*args,  **kwargs)

    return wrapper

class StatusChecker(AbstractHandler):
    def __init__(self) -> None:
        self.rcm = RedisCacheManager()

    @timer
    def checkDatabase(self):
        query_keys = ["process_id", "process_name", "session_id", "stream_id", "aos_type_id", "player_id", "court_id", "limit", "force"]
        QUERY = f'''SELECT p.id, p.name, s.id, s.stream_id, s.aos_type_id, s.player_id, s.court_id, s."limit", s."force" FROM public."Process" as p INNER JOIN public."SessionParameter" as s ON p.session_id = s.id WHERE p.is_completed=false'''
        processData = self.rcm.Read(query=QUERY, force=True)
        processes = bytes2obj(processData)

        return [dict(zip(query_keys, process)) for process in processes]
    
    def handle(self, data: Any):
        data: list = self.checkDatabase()
        return super().handle(data)
