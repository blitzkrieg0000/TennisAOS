from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, request) -> Optional[str]:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any) -> str:
        if self._next_handler:
            return self._next_handler.handle(request)
        return request



class FaceDetector(AbstractHandler):
    def handle(self, request: Any) -> str:
        request += " -> Detector"
        return super().handle(request)

class FaceRecognizer(AbstractHandler):
    def handle(self, request: Any) -> str:
        request += " -> Kişi"
        return super().handle(request)

class FaceDrawer(AbstractHandler):
    def handle(self, request: Any) -> str:
        request += " -> Çiz"
        return super().handle(request)

class FaceSaver(AbstractHandler):
    def handle(self, request: Any) -> str:
        request += " -> Kaydet"
        return super().handle(request)



if __name__ == "__main__":
    faceDrawer = FaceDrawer()
    faceDetector = FaceDetector()
    faceRecognizer = FaceRecognizer()
    faceSaver = FaceSaver()

    var = faceDetector.set_next(faceRecognizer).set_next(faceDrawer).set_next(faceSaver)

    result = faceDetector.handle("Başla")

    print(result)