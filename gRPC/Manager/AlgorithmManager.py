import base64
import hashlib as hl
import pickle
import time

import cv2
import numpy as np

import mainRouterServer_pb2 as rc
from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Postgres.postgres_client import PostgresDatabaseClient
from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from clients.TrackBall.tb_client import TBClient
from libs.EncodeManager import EncodeManager
from libs.logger import logger


class AlgorithmManager():
    EXCEPT_PREFIX = ['']
    def __init__(self):
        super().__init__()
        self.kpm  = KafkaProducerManager()
        self.pdc = PostgresDatabaseClient()
        self.rcm = RedisCacheManager()
        self.dclc = DCLClient()
        self.kcm = KafkaConsumerManager()
        self.tbc = TBClient()
        self.pfpc = PFPClient()
        self.processDataClient = PDClient()
        self.encodeManager = EncodeManager()


    #! TOOLS
    # Converters---------------------------------------------------------------
    def bytes2obj(self, bytes):
        if bytes is not None or bytes != b'':
            return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def byte2frame(self, bytes_frame):
        nparr = np.frombuffer(bytes_frame, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame

    def frame2bytes(self, frame):
        res, encodedImg = cv2.imencode('.jpg', frame)
        return encodedImg.tobytes()

    def frame2base64(self, frame):
        if frame is None:
            return None
        etval, buffer = cv2.imencode('.png', frame)
        Base64Img = base64.b64encode(buffer)
        return Base64Img

    def convertPoint2ProtoCustomArray(self,lineArray):
        #TODO Serialize
        LinePackage = rc.linePackage()
        for i, line in enumerate(lineArray):
            if len(line)>0:
                Line = rc.line()
                Line.items.extend([rc.number(data=line[0]), rc.number(data=line[1]), rc.number(data=line[2]), rc.number(data=line[3])])
                LinePackage.items.extend([Line])
            if i==10:
                break
        return LinePackage

    def createResponseData(self, frame, courtPoints):
        frame = self.drawLines(frame, courtPoints)
        Base64Img = self.frame2base64(frame)
        return courtPoints, Base64Img

    # Redis-Postgresql---------------------------------------------------------
    def getUID(self):
        return int.from_bytes(hl.md5(str(time.time()).encode("utf-8")).digest(), "big")

    def getTopicName(self, prefix, id):
        prefix = prefix.replace("-","_")
        if prefix in self.EXCEPT_PREFIX:
            return prefix
        return f"{prefix}-{id}-{self.getUID()}"

    def getStreamData(self, id):
        query_keys = ["stream_name", "source", "court_line_array", "kafka_topic_name"]
        QUERY = f'SELECT name, source, court_line_array, kafka_topic_name FROM public."Stream" WHERE id={id} AND is_activated=true'
        streamData = self.rcm.Read(query=QUERY, force=False)
        streamData = self.bytes2obj(streamData)
        if streamData is not None:
            return [dict(zip(query_keys, item)) for item in streamData]
        assert "Stream Bilgisi Bulunamadı."

    def getCourtPointAreaId(self, AOS_TYPE_ID):
        query_keys = ["aos_type_name", "court_point_area_id" ]
        QUERY = f'SELECT name, court_point_area_id FROM public."AOSType" WHERE id={AOS_TYPE_ID}'
        streamData = self.rcm.Read(query=QUERY, force=False)
        streamData = self.bytes2obj(streamData)
        if streamData is not None:
            return [dict(zip(query_keys, item)) for item in streamData]
        return None

    def saveTopicName(self, stream_id, newTopicName):
        return self.rcm.Write(f'UPDATE public."Stream" SET kafka_topic_name=%s WHERE id={stream_id};', [newTopicName,])

    def saveCourtLinePoints(self, stream_id, courtPoints):
        return self.rcm.Write(f'UPDATE public."Stream" SET court_line_array=%s WHERE id={stream_id};', [courtPoints,])

    def savePlayingData(self, data):
        return self.rcm.Write(
        'INSERT INTO public."PlayingData"(player_id, court_id, aos_type_id, stream_id, score, ball_position_area, player_position_area, ball_fall_array) \
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
        [data["player_id"],data["court_id"],data["aos_type_id"],data["stream_id"],data["score"],data["ball_position_area"],data["player_position_area"],data["ball_fall_array"] ]) 

    # Canvas-------------------------------------------------------------------
    def drawLines(self, cimage, points):
        if points is None:
            return cimage

        for i, line in enumerate(points):
            if len(line)>0:
                cimage = cv2.line(cimage, ( int(line[0]), int(line[1]) ), ( int(line[2]), int(line[3]) ), (66, 245, 102), 3)
            if i==10:
                break
        return cimage


    #! Main Server
    # Manage Producer----------------------------------------------------------
    def getProducerThreads(self, request, context):
        return rc.responseData(data=self.kpm.getProducerThreads())

    def stopProduce(self, request, context):
        #Bu topic producer çalışıyorsa durdur.
        self.kpm.stopProduce(f'streaming_thread_{request.data}')
        return rc.responseData(data=b"TRYING STOP PRODUCER...")

    def stopAllProducerThreads(self, request, context):
        msg = self.kpm.stopAllProducerThreads()
        return rc.responseData(data=b"TRYING STOP PRODUCERS...")

    # Manage Consumer----------------------------------------------------------
    def getRunningConsumers(self, request, context):
        return rc.responseData(data=self.kcm.getRunningConsumers()) 

    def stopRunningConsumer(self, request, context):
        msg = self.kcm.stopRunningCosumer(request.data)
        return rc.responseData(data=b"TRYING STOP CONSUMER...")

    def stopAllRunningConsumers(self, request, context):
        msg = self.kcm.stopAllRunningConsumers()
        return rc.responseData(data=b"TRYING STOP CONSUMERS...")

    # Algorithms---------------------------------------------------------------  
    def detectCourtLinesController(self, data):
        #! 1-REDIS: 
        # Stream bilgilerini al
        streamData = self.getStreamData(data["stream_id"])[0]

        if len(streamData)>0:
            courtPoints = None
            SerializedCourtPoints = None
            newTopicName = self.getTopicName(streamData["stream_name"], 0) # Unique name
            
            # TODO Hata olduğunda servis isteğini sonlandırmak için gerekli hamleleri yap.
            # self.topicGarbageCollector(context, newTopicName)

            #! 2-REDIS:
            # TOPIC ismini kaydet
            res = self.saveTopicName(data["stream_id"], newTopicName)

            #! 3-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newTopicName, streamData["source"], limit=1)
            
            #! 4-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newTopicName, "consumergroup-courtlinedetector-0", 1, False)

            #! 5-COURT_LINE_DETECTOR:
            # Tenis sahasının çizgilerini bul
            frame = []
            for bytes_frame in BYTE_FRAMES_GENERATOR:
                frame = self.byte2frame(bytes_frame.data)

                if streamData["court_line_array"] is not None and streamData["court_line_array"] != "" and not data["force"]:
                    line_arrays = self.encodeManager.deserialize(streamData["court_line_array"])
                    frame = self.drawLines(frame, line_arrays)
                    return line_arrays, self.frame2bytes(frame)

                courtPoints = self.dclc.extractCourtLines(image=bytes_frame.data)

            #! 6-REDIS:
            # Tenis çizgilerini postgresqle kaydet
            if courtPoints is not None:
                SerializedCourtPoints = self.encodeManager.serialize(self.bytes2obj(courtPoints))
                self.saveCourtLinePoints(data["stream_id"], SerializedCourtPoints)
            
            # DeleteTopic
            self.kpm.deleteTopics([newTopicName])

            frame = self.drawLines(frame, courtPoints)
            return courtPoints, self.frame2bytes(frame)
        else:
            assert "Stream Data (ID={}) Not Found".format(data["stream_id"])

    def StartGameObservationController(self, data):
        allData = {}

        #! 1-REDIS
        # Stream bilgilerini al
        streamData = self.getStreamData(data["stream_id"])[0]
        
        if len(streamData)>0:

            newTopicName = self.getTopicName(streamData["kafka_topic_name"], 0)
            res = self.saveTopicName(data["stream_id"], newTopicName)

            #! 2-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newTopicName, streamData["source"], limit=data["limit"])
            
            #! 3-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newTopicName, "consumergroup-balltracker-0", -1, False)

            all_points = []
            last_frame = None
            for bytes_frame in BYTE_FRAMES_GENERATOR:
                
                #TODO TrackNet modülünü HIZLANDIR.( findTennisBallPosition )
                #! 4-TRACKBALL (DETECTION)

                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!
                all_points.append(self.bytes2obj(balldata))
                last_frame = bytes_frame.data
            
            if last_frame is None:
                assert "last_frame is None"

            # PREDICT BALL POSITION
            fall_points = self.pfpc.predictFallPosition(all_points)
            
            allData["ball_fall_array"] = fall_points

            #PROCESS DATA
            court_point_area_data = self.getCourtPointAreaId(data["aos_type_id"])[0]

            processData = {}
            processData["fall_point"] = self.bytes2obj(fall_points)
            processData["court_lines"], canvas = self.detectCourtLinesController(data)
            processData["court_point_area_id"] = court_point_area_data["court_point_area_id"]

            canvas, processedData = self.processDataClient.processAOS(image=canvas, data=processData)
            processedData = self.bytes2obj(processedData)

            allData["score"] = processedData["score"]
            allData["ball_position_area"] = self.obj2bytes(all_points)
            allData["player_position_area"] = self.obj2bytes([])
            allData["stream_id"] = data["stream_id"]
            allData["aos_type_id"] = data["aos_type_id"]
            allData["player_id"] = data["player_id"]
            allData["court_id"] = data["court_id"]

            # SAVE DATA
            self.savePlayingData(allData)
            
            # CreateResponse
            canvas = self.byte2frame(canvas)
            return processData, self.frame2base64(canvas)