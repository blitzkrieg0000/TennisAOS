import base64
import hashlib
import pickle
import time

import cv2
import numpy as np

from clients.Redis.redis_client import RedisCacheManager

#* Gelen Argümanlardan herhangi birisi None ise None döndür.
def checkNull(func):
    def wrapper(*args, **kwargs):
        if not all( [False for val in kwargs.values() if val is None]): return None
        if not all( [False for arg in args if arg is None]): return None
        return func(*args, **kwargs)
    return wrapper

#* Class Wrapper, class altındaki tüm methodlar için ilgili decoratorı tanımlar.
def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


@for_all_methods(checkNull)
class Converters():
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def bytes2obj(bytes):
        if bytes != b'':
            return pickle.loads(bytes)
        return None

    @staticmethod
    def obj2bytes(obj):
        return pickle.dumps(obj)
    
    @staticmethod
    def bytes2frame(bytes_frame):
        nparr = np.frombuffer(bytes_frame, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    @staticmethod
    def frame2bytes(frame):
        res, encodedImg = cv2.imencode('.jpg', frame)
        return encodedImg.tobytes()
    
    @staticmethod
    def frame2base64(frame):
        etval, buffer = cv2.imencode('.png', frame)
        return base64.b64encode(buffer)


@for_all_methods(checkNull)
class Tools():
    EXCEPT_PREFIX = ['']
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def getUID():
        return int.from_bytes(hashlib.md5(str(time.time()).encode("utf-8")).digest(), "little")

    @staticmethod
    def generateTopicName(prefix, id):
        prefix = prefix.replace("-","_")
        if prefix in Tools.EXCEPT_PREFIX:
            return prefix
        return f"{prefix}-{id}-{Tools.getUID()}"

    @staticmethod
    def drawLines(cimage, points):
        for i, line in enumerate(points):
            if len(line)>0:
                cimage = cv2.line(cimage, ( int(line[0]), int(line[1]) ), ( int(line[2]), int(line[3]) ), (66, 245, 102), 3)
            if i==10:
                break
        return cimage


@for_all_methods(checkNull)
class Repositories():
    def __init__(self) -> None:
        self.rcm = RedisCacheManager()

    def getStreamData(self, manager, id):
        query_keys = ["stream_name", "source", "court_line_array", "kafka_topic_name"]
        QUERY = f'SELECT name, source, court_line_array, kafka_topic_name FROM public."Stream" WHERE id={id} AND is_activated=true'
        streamData = manager.Read(query=QUERY, force=False)
        streamData = Converters.bytes2obj(streamData)
        if streamData is not None:
            return [dict(zip(query_keys, item)) for item in streamData]
        assert "Stream Bilgisi Bulunamadı."

    def getCourtPointAreaId(self, manager, AOS_TYPE_ID):
        query_keys = ["aos_type_name", "court_point_area_id" ]
        QUERY = f'SELECT name, court_point_area_id FROM public."AOSType" WHERE id={AOS_TYPE_ID}'
        streamData = manager.Read(query=QUERY, force=False)
        streamData = self.bytes2obj(streamData)
        if streamData is not None:
            return [dict(zip(query_keys, item)) for item in streamData]
        return None

    def saveTopicName(self, manager, stream_id, newTopicName):
        return manager.Write(f'UPDATE public."Stream" SET kafka_topic_name=%s WHERE id={stream_id};', [newTopicName,])

    def saveCourtLinePoints(self,manager, stream_id, courtPoints):
        return manager.Write(f'UPDATE public."Stream" SET court_line_array=%s WHERE id={stream_id};', [courtPoints,])

    def savePlayingData(self,manager, data):
        return manager.Write(
        'INSERT INTO public."PlayingData"(player_id, court_id, aos_type_id, stream_id, score, ball_position_area, player_position_area, ball_fall_array) \
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
        [data["player_id"],data["court_id"],data["aos_type_id"],data["stream_id"],data["score"],data["ball_position_area"],data["player_position_area"],data["ball_fall_array"] ]) 