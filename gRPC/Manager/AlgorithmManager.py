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

    # HELPERS------------------------------------------------------------------
    def bytes2obj(self, bytes):

        logger.info(str(bytes))
        if bytes is not None or bytes != b'':
            return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def byte2frame(self, bytes_frame):
        nparr = np.frombuffer(bytes_frame, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame

    def getUID(self):
        return int.from_bytes(hl.md5(str(time.time()).encode("utf-8")).digest(), "big")

    def getTopicName(self, prefix, id):
        prefix = prefix.replace("-","_")
        if prefix in self.EXCEPT_PREFIX:
            return prefix
        return f"{prefix}-{id}-{self.getUID()}"

    def getStreamData(self, id):
        QUERY = f'''SELECT name, source, court_line_array, kafka_topic_name FROM public."Stream" WHERE id={id} AND is_activated=true'''
        streamData = self.rcm.Read(query=QUERY, force=False)
        streamData = self.bytes2obj(streamData)
        
        return streamData

    def getCourtPointAreaId(self, AOS_TYPE_ID):
        QUERY = f'''SELECT name, court_point_area_id FROM public."AOSType" WHERE id={AOS_TYPE_ID}'''
        streamData = self.rcm.Read(query=QUERY, force=False)
        streamData = self.bytes2obj(streamData)
        return streamData

    def saveTopicName(self, stream_id, newCreatedTopicName):
        return self.rcm.writeCache(f'UPDATE public."Stream" SET kafka_topic_name=%s WHERE id={stream_id};', [newCreatedTopicName,])

    def saveCourtLinePoints(self, stream_id, courtPoints):
        return self.rcm.writeCache(f'UPDATE public."Stream" SET court_line_array=%s WHERE id={stream_id};', [courtPoints,])

    def savePlayingData(self, data):
        return self.rcm.writeCache(
        f'''INSERT INTO public."PlayingData"(player_id, court_id, aos_type_id, stream_id, score, ball_position_area, player_position_area, ball_fall_array) \
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',
        [data["player_id"],data["court_id"],data["aos_type_id"],data["stream_id"],data["score"],data["ball_position_area"],data["player_position_area"],data["ball_fall_array"] ]) 

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

    def drawLines(self, cimage, points):
        for i, line in enumerate(points):
            if len(line)>0:
                cimage = cv2.line(cimage, ( int(line[0]), int(line[1]) ), ( int(line[2]), int(line[3]) ), (66, 245, 102), 3)
            if i==10:
                break
        return cimage

    def frame2base64(self, frame):
        etval, buffer = cv2.imencode('.png', frame)
        Base64Img = base64.b64encode(buffer)
        return Base64Img

    def createResponseData(self, frame, courtPoints):
        courtPoints = self.bytes2obj(courtPoints)
        frame = self.drawLines(frame, courtPoints)
        Base64Img = self.frame2base64(frame)
        LineProto = self.convertPoint2ProtoCustomArray(courtPoints)
        response = rc.LinesResponseData(lines=LineProto, frame=Base64Img)
        return response


    # ALGORITHMS---------------------------------------------------------------
    # p.id, s.id, s.stream_id, s.aos_type_id, s.player_id, s.court_id, s."limit", s."force"
    def StartGameObservationController(self, data):

        allData = {}

        #! 1-REDIS
        # Stream bilgilerini al
        streamData = self.getStreamData(data["stream_id"])

        if len(streamData)>0:
            topicName = streamData[0]
            streamName = streamData[1]

            newCreatedTopicName = self.getTopicName(topicName, 0)
            
            res = self.saveTopicName(data["stream_id"], newCreatedTopicName)

            #! 2-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newCreatedTopicName, streamName, limit=data["limit"])
            
            #! 3-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newCreatedTopicName, "consumergroup-balltracker-0", -1, False)

            all_points = []
            last_frame = None
            for bytes_frame in BYTE_FRAMES_GENERATOR:
                
                #TODO TrackNet modülünü HIZLANDIR.( findTennisBallPosition )
                #! 4-TRACKBALL (DETECTION)

                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newCreatedTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!

                all_points.append(self.bytes2obj(balldata))

                last_frame = bytes_frame.data

            if last_frame is None:
                assert "last_frame is None"

            # PREDICT BALL POSITION
            fall_points = self.pfpc.predictFallPosition(all_points)
            
            allData["ball_fall_array"] = fall_points

            #PROCESS DATA
            court_point_area_data = self.getCourtPointAreaId(data["aos_type_id"])
            processData = {}
            processData["fall_point"] = self.bytes2obj(fall_points)
            processData["court_lines"] = self.bytes2obj(streamData[2])
            processData["court_point_area_id"] = court_point_area_data[1]
            canvas, processedData = self.processDataClient.processAOS(image=last_frame, data=processData)
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
            response = rc.gameObservationControllerResponse()
            
            if processData["fall_point"] is not None:
                for item in processData["fall_point"]:
                    cv2.circle(canvas, (int(item[0]),int(item[1])), 3, (0,255,0), -1)
                    point = rc.point(x=item[0], y=item[1])
                    response.fallPoints.extend([point])
            else:
                point = rc.point(x=-1, y=-1)
                response.fallPoints.extend([point])

            if processedData["score"] is not None:
                response.score = processedData["score"]
            else:
                response.score = 0
                
            response.frame=self.frame2base64(canvas)
        return response

    def getProducerThreads(self, request, context):
        return rc.responseData(data=self.kpm.getProducerThreads())

    def stopProduce(self, request, context):
        #Bu topic producer çalışıyorsa durdur.
        self.kpm.stopProduce(f'streaming_thread_{request.data}')
        return rc.responseData(data=b"TRYING STOP PRODUCER...")

    def stopAllProducerThreads(self, request, context):
        msg = self.kpm.stopAllProducerThreads()
        return rc.responseData(data=b"TRYING STOP PRODUCERS...")

    def getRunningConsumers(self, request, context):
        return rc.responseData(data=self.kcm.getRunningConsumers()) 

    def stopRunningConsumer(self, request, context):
        msg = self.kcm.stopRunningCosumer(request.data)
        return rc.responseData(data=b"TRYING STOP CONSUMER...")

    def stopAllRunningConsumers(self, request, context):
        msg = self.kcm.stopAllRunningConsumers()
        return rc.responseData(data=b"TRYING STOP CONSUMERS...")