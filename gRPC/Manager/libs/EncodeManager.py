import json
from json import JSONEncoder
import numpy as np

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class EncodeManager():
    def serialize(self, arr):
        return json.dumps(arr, cls=NumpyArrayEncoder)

    def deserialize(self, arr):
        decodedArrays = json.loads(arr)
        return decodedArrays #np.asarray(decodedArrays)

if __name__ == "__main__":
    em = EncodeManager()
    #arr = np.array([[10,20], [20,30], [None,None]])

    arr = {"value":["value-1", 1, 3.4, [[1,2],[2,3]]], "type" : ["str", "int", "float", "bytes"]}
    

    # serialized = em.serialize(arr)
    # print(type(serialized))
    # deserialized = em.deserialize(serialized)
    # print(deserialized["value"])