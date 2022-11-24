from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class Handler(ABC):
    @abstractmethod
    def SetNext(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def Handle(self, **kwargs) -> Optional[dict]:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def SetNext(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def Handle(self, **kwargs: Any):
        if self._next_handler:
            return self._next_handler.Handle(**kwargs)
        return kwargs