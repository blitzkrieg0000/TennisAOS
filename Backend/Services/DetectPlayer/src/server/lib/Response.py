from enum import Enum
from typing import Any


class ResponseCodes(Enum):
    SUCCESS = 0
    WARNING = 1
    ERROR = 2
    INFO = 3
    NULL = 4
    NOT_FOUND = 5
    REQUIRED = 6
    UNSUFFICIENT = 7
    CONNECTION_ERROR = 8



class  CreateResponse():
    def __init__(self, rc) -> None:
        self.rc = rc

    def __call__(self, code:ResponseCodes, message:str="", data:Any=None) -> Any:
        response = self.rc.Response()
        response.Code = self.rc.Response.ResponseCodes.Value(code.name)
        response.Message = message
        response.Data = data
        return response


