from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional



class Handler():
    classVar = "Class-Base"
    def __init__(self) -> None:
        self.instanceVar = "Instance-Base"


class ApplyAlgorithms(Handler):
    def __init__(self) -> None:
        super().__init__()



if "__main__" == __name__:
    First = ApplyAlgorithms()
    Second = ApplyAlgorithms()

    print(First.instanceVar)
