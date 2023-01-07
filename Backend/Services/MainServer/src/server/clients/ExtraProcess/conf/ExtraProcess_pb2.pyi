from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ExtraProcessRequest(_message.Message):
    __slots__ = ["Data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    Data: bytes
    def __init__(self, Data: _Optional[bytes] = ...) -> None: ...

class ExtraProcessResponse(_message.Message):
    __slots__ = ["Message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    Message: str
    def __init__(self, Message: _Optional[str] = ...) -> None: ...
