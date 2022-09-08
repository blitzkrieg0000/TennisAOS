from __future__ import annotations

import time
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Converters
from libs.base import AbstractHandler
import logging


INTERVAL = 3 # Second(s)

class StatusChecker(AbstractHandler):
    def __init__(self) -> None:
        self.rcm = RedisCacheManager()

    def timer(func):
        def wrapper(self, *args, **kwargs):
            time.sleep(INTERVAL)
            logging.info("Yeni Processler Kontrol Ediliyor...")
            return func(self, *args,  **kwargs)

        return wrapper

    @timer
    def checkDatabase(self):
        query_keys = ["process_id", "process_name", "session_id", "stream_id", "aos_type_id", "player_id", "court_id", "limit", "force","stream_name", "source", "court_line_array", "kafka_topic_name", "is_video"]
        QUERY = f'SELECT p.id as process_id, p.name as process_name, sp.id as session_id, st.id, sp.aos_type_id, sp.player_id, sp.court_id,sp."limit", sp."force", st."name", st."source", st.court_line_array, st.kafka_topic_name, st.is_video\
        FROM public."Process" as p\
        INNER JOIN public."SessionParameter" as sp\
        ON sp.id = p.session_id\
        INNER JOIN public."ProcessParameters" as pp\
        ON pp.id = p.id\
        INNER JOIN public."Stream" as st\
        ON (CASE WHEN pp.stream_id IS NULL THEN st.id = sp.stream_id ELSE st.id = pp.stream_id END)\
        WHERE p.is_completed=false AND st.is_video=true'
        processData = self.rcm.Read(query=QUERY, force=True)
        processes = Converters.bytes2obj(processData)
        if processes is not None:
            return [dict(zip(query_keys, process)) for process in processes]
        return []
    
    def handle(self, data: Any):
        data: list = self.checkDatabase()
        return super().handle(data)
