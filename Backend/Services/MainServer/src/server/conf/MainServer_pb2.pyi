from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class MergeDataRequestData(_message.Message):
    __slots__ = ["ProcessId"]
    PROCESSID_FIELD_NUMBER: _ClassVar[int]
    ProcessId: float
    def __init__(self, ProcessId: _Optional[float] = ...) -> None: ...

class MergeDataResponseData(_message.Message):
    __slots__ = ["Message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    Message: str
    def __init__(self, Message: _Optional[str] = ...) -> None: ...

class StartProcessRequestData(_message.Message):
    __slots__ = ["ProcessId"]
    PROCESSID_FIELD_NUMBER: _ClassVar[int]
    ProcessId: float
    def __init__(self, ProcessId: _Optional[float] = ...) -> None: ...

class StartProcessResponseData(_message.Message):
    __slots__ = ["Data", "Frame", "Message"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    Data: str
    FRAME_FIELD_NUMBER: _ClassVar[int]
    Frame: str
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    Message: str
    def __init__(self, Message: _Optional[str] = ..., Data: _Optional[str] = ..., Frame: _Optional[str] = ...) -> None: ...

class StopProcessRequestData(_message.Message):
    __slots__ = ["ProcessId"]
    PROCESSID_FIELD_NUMBER: _ClassVar[int]
    ProcessId: float
    def __init__(self, ProcessId: _Optional[float] = ...) -> None: ...

class StopProcessResponseData(_message.Message):
    __slots__ = ["Message", "flag"]
    FLAG_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    Message: str
    flag: bool
    def __init__(self, Message: _Optional[str] = ..., flag: bool = ...) -> None: ...
