from __future__ import annotations

import time
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Converters
from libs.base import AbstractHandler
import logging


INTERVAL = 3 # Second(s)

def timer(func):
    def wrapper(*args, **kwargs):
        time.sleep(INTERVAL)
        
        logging.info("Yeni Processler Kontrol Ediliyor...")
        return func(*args,  **kwargs)

    return wrapper

class StatusChecker(AbstractHandler):
    def __init__(self) -> None:
        self.rcm = RedisCacheManager()

    @timer
    def checkDatabase(self):
        query_keys = ["process_id", "process_name", "session_id", "stream_id", "aos_type_id", "player_id", "court_id", "limit", "force","stream_name", "source", "court_line_array", "kafka_topic_name", "is_video"]
        QUERY = f'SELECT p.id, p.name, s.id, s.stream_id, s.aos_type_id, s.player_id, s.court_id, s."limit", s."force", st."name", st."source" , st.court_line_array, st.kafka_topic_name, st.is_video\
                FROM public."Process" as p\
                INNER JOIN public."SessionParameter" as s\
                ON p.session_id = s.id\
                INNER JOIN public."Stream" as st\
                on st.id =  s.stream_id\
                WHERE p.is_completed=false'
        processData = self.rcm.Read(query=QUERY, force=True)
        processes = Converters.bytes2obj(processData)
        if processes is not None:
            return [dict(zip(query_keys, process)) for process in processes]
        return []
    
    def handle(self, data: Any):
        data: list = self.checkDatabase()
        return super().handle(data)
