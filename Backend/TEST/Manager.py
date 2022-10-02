from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional


class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, *args:tuple[tuple, ...], **kwargs: dict[str, Any]) -> Optional[str]:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, *args:tuple[tuple, ...], **kwargs: dict[str, Any]) -> str:
        if self._next_handler:
            return self._next_handler.handle(*args, **kwargs)
        return args, kwargs


class StatusChecker(AbstractHandler):
    
    def checkDatabase(self):
        data = {}
        
        return data
    
    def handle(self, data: Any) -> str:
        data: dict = self.checkDatabase()
        time.sleep(10)

        return super().handle(data)


class ProcessManager(AbstractHandler):
    
    processList = []

    def process(self, data):
        #Zaman alan bir görüntü işleme ...
        time.sleep(10)

    def handle(self, data: Any) -> str:

        data: dict = self.process(data)
        
        return super().handle(data)


if __name__ == "__main__":

    sc = StatusChecker()
    pm =  ProcessManager()
    results = sc.set_next(pm).set_next(sc).handle({})
