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
    all_points = []
    arr = np.array([[None, None], [None, None], [879, 525], [None, None], [906.5, 505.5], [905.5, 504.5], [933.5, 483.5],
     [932.5, 484.5], [None, None], [960.5, 465.5], [959.5, 465.5], [982.5, 448.5], [983.5, 450.5], [1005.5, 440.5],
      [1004.5, 440.5], [None, None], [1022.5, 433.5], [1024.5, 433.5], [1043.5, 425.5], [1042.5, 424.5], [1042, 424],
       [1060.5, 418.5], [1059.5, 417.5], [1076.5, 416.5], [1076, 417], [1091.5, 412.5], [1093.5, 414.5], [None, None],
        [1107.5, 412.5], [1105.5, 413.5], [1123.5, 414.5], [1122.5, 414.5], [None, None], [1130.5, 400.5], [1131, 400],
         [1140.5, 377.5], [1142.5, 377.5], [1149.5, 357.5], [1149, 358], [1148.5, 359.5], [1156.5, 337.5], [1156.5, 339.5],
          [1162.5, 327.5], [1164.5, 327.5], [None, None], [1173.5, 309.5], [1172.5, 308.5], [1177.5, 297.5], [1176.5, 298.5],
           [1184.5, 288.5], [1186.5, 288.5], [None, None], [1192.5, 279.5], [1194.5, 280.5], [1200.5, 271.5], [1199.5, 269.5],
            [None, None], [1202.5, 267.5], [1204.5, 267.5], [1211.5, 260.5]])
    all_points.append(arr)
    all_points.append(arr)
    #arr = {"value":["value-1", 1, 3.4, [[1,2],[2,3]]], "type" : ["str", "int", "float", "bytes"]}
    

    serialized = em.serialize(all_points)
    print(type(serialized), serialized )

    deserialized = em.deserialize(serialized)
    print(type(deserialized), deserialized )