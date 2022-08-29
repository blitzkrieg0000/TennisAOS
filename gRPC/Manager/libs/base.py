from __future__ import annotations
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
    def handle(self, *args:tuple[tuple, ...], **kwargs: dict[str, Any]):
        if self._next_handler:
            return self._next_handler.handle(*args, **kwargs)
        return args, kwargs