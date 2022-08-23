import json
from json import JSONEncoder
import numpy as np

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class Serializer():
    def serialize(self, arr):
        return json.dumps(arr, cls=NumpyArrayEncoder)

    def deserialize(self, arr):
        decodedArrays = json.loads(arr)
        return np.asarray(decodedArrays)

if __name__ == "__main__":
    serializerManager = Serializer()
    arr = np.array([[10,20], [20,30], [None,None]])
    serialized = serializerManager.serialize(arr)
    print(type(serialized))
    deserialized = serializerManager.deserialize(serialized)
    print(deserialized)