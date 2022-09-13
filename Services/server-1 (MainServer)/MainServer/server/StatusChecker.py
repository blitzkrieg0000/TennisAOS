from __future__ import annotations

import time
from typing import Any

from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Converters, Repositories
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
        return Repositories.getAllProcessRelated(self.rcm)
    
    def handle(self, data: Any):
        data: list = self.checkDatabase()
        return super().handle(data)
