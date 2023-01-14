import json
import os
import inspect
import pickle
import numpy as np


def CWD():
    """Bu fonksiyonu çağıran dosyanın konumunu al"""
    p = "/"
    try: p = os.path.abspath(os.path.dirname(inspect.stack()[1][1]))
    except Exception as e: pass
    return p



#* Gelen Argümanlardan herhangi birisi None ise None döndür.
def CheckNull(func):
    def wrapper(*args, **kwargs):
        if not all( [False for val in kwargs.values() if val is None]): return None
        if not all( [False for arg in args if arg is None]): return None
        return func(*args, **kwargs)
    return wrapper

#* Class Wrapper, class altındaki tüm methodlar için ilgili decoratorı tanımlar.
def ForAllMethods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate

@ForAllMethods(CheckNull)
class Converters():
    def __init__(self) -> None:
        pass
    

    @staticmethod
    def Bytes2Obj(bytes):
        if bytes != b'':
            return pickle.loads(bytes)
        return None


    @staticmethod
    def Obj2Bytes(obj):
        return pickle.dumps(obj)


    @staticmethod
    def Ndarray2Bytes(frame: np.ndarray):
        if(frame.dtype != np.uint8):
            return None
        h, w, c = frame.shape
        byteArray = np.ndarray.tobytes(frame)
        return byteArray, h, w, c


    @staticmethod
    def Bytes2Ndarray(byteImg, h, w, c):
        temp = np.frombuffer(byteImg, dtype=np.uint8)
        reshapedImg = np.reshape(temp, (h, w, c))
        return reshapedImg

class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


@ForAllMethods(CheckNull)
class EncodeManager():
    def __init__(self) -> None:
        pass
    

    @staticmethod
    def Serialize(arr):
        return json.dumps(arr, cls=NumpyArrayEncoder)


    @staticmethod
    def Deserialize(arr):
        decodedArrays = json.loads(arr)
        return decodedArrays #np.asarray(decodedArrays)