import base64
import hashlib as hl
from libs.logger import logger
import pickle
import time
from concurrent import futures
import cv2
import grpc
import numpy as np
import mainRouterServer_pb2 as rc
import mainRouterServer_pb2_grpc as rc_grpc
from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Postgres.postgres_client import PostgresDatabaseClient
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from clients.TrackBall.tb_client import TBClient
from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient

class MainServer(rc_grpc.mainRouterServerServicer):
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
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2Frame(self, img):
        nparr = np.frombuffer(img, np.uint8)
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
        streamData = self.rcm.isCached(query=QUERY)
        streamData = self.bytes2obj(streamData)
        return streamData

    def getCourtPointAreaId(self, AOS_TYPE_ID):
        QUERY = f'''SELECT name, court_point_area_id FROM public."AOSType" WHERE id={AOS_TYPE_ID}'''
        streamData = self.rcm.isCached(query=QUERY)
        streamData = self.bytes2obj(streamData)
        return streamData

    def saveTopicName(self, stream_id, newCreatedTopicName):
        return self.rcm.writeCache(f'UPDATE public."Stream" SET kafka_topic_name=%s WHERE id={stream_id};', [newCreatedTopicName,])

    def saveCourtLinePoints(self, stream_id, courtPoints):
        return self.rcm.writeCache(f'UPDATE public."Stream" SET court_line_array=%s WHERE id={stream_id};', [courtPoints,])

    def savePlayingData(self, stream_id, data):
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

    def byte2frame(self, bytes_frame):
        nparr = np.frombuffer(bytes_frame, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame

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

    def topicGarbageCollector(self, context, newCreatedTopicName):
        def cb():
            logger.warning(f"Sonlanan işlem: {newCreatedTopicName}")
            self.kpm.stopProduce(f"streaming_thread_{newCreatedTopicName}")
            self.kcm.stopRunningCosumer(newCreatedTopicName)
            self.tbc.deleteDetector(newCreatedTopicName)
            self.kpm.deleteTopics([newCreatedTopicName])
        context.add_callback(cb)
    
    def createResponseData(self, frame, courtPoints):
        courtPoints = self.bytes2obj(courtPoints)
        frame = self.drawLines(frame, courtPoints)
        Base64Img = self.frame2base64(frame)
        LineProto = self.convertPoint2ProtoCustomArray(courtPoints)
        response = rc.LinesResponseData(lines=LineProto, frame=Base64Img)
        return response

    # ALGORITHMS---------------------------------------------------------------
    def detectCourtLinesController(self, request, context):

        #! REDIS: 
        # Stream bilgilerini al
        streamData = self.getStreamData(request.id)

        if len(streamData)>0:
            streamName = streamData[0]
            streamUrl = streamData[1]
            courtPoints = streamData[2]

            newCreatedTopicName = self.getTopicName(streamName, 0) # İşlenecek Görüntüler için Unique bir isim

            self.topicGarbageCollector(context, newCreatedTopicName)

            #! 2-REDIS:
            # TOPIC ismini kaydet
            res = self.saveTopicName(request.id, newCreatedTopicName)

            #! 3-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newCreatedTopicName, streamUrl, limit=1)
            
            #! 4-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newCreatedTopicName, "consumergroup-courtlinedetector-0", 1, False)

            #! 5-COURT_LINE_DETECTOR:
            # Tenis sahasının çizgilerini bul
            frame = []
            for bytes_frame in BYTE_FRAMES_GENERATOR:
                frame = self.byte2frame(bytes_frame.data)

                if courtPoints is not None and not request.force:
                    return self.createResponseData(frame, courtPoints)

                courtPoints = self.dclc.extractCourtLines(image=bytes_frame.data)

            #! 6-REDIS:
            # Tenis çizgilerini postgresqle kaydet
            self.saveCourtLinePoints(request.id, courtPoints)
            
            # DeleteTopic
            self.kpm.deleteTopics([newCreatedTopicName])
            logger.info("INFO: ",courtPoints)
            return self.createResponseData(frame, courtPoints)
        else:
            assert "Stream Data (ID={}) Not Found".format(request.id)


    def gameObservationController(self, request, context):
        receivedData = self.bytes2obj(request.data)

        #! 1-REDIS
        # Stream bilgilerini al
        streamData = self.getStreamData(receivedData)
        
        if len(streamData)>0:
            topicName = streamData[0]
            streamName = streamData[1]

            newCreatedTopicName = self.getTopicName(topicName, 0)
            self.topicGarbageCollector(context, newCreatedTopicName)
            res = self.saveTopicName(receivedData["id"], newCreatedTopicName)

            #! 2-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newCreatedTopicName, streamName, limit=receivedData["limit"])
            
            #! 3-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newCreatedTopicName, "consumergroup-balltracker-0", -1, False)

            all_points = []
            last_frame = []
            for bytes_frame in BYTE_FRAMES_GENERATOR:
                
                #TODO TrackNet modülünü HIZLANDIR.( findTennisBallPosition )
                #! 4-TRACKBALL (DETECTION)
                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newCreatedTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!

                points = self.bytes2obj(balldata)
                all_points.append(points)

                last_frame = bytes_frame.data


            # PREDICT BALL POSITION
            fall_points = self.pfpc.predictFallPosition(all_points)

            #PROCESS DATA
            court_point_area_data = self.getCourtPointAreaId(receivedData["aos_type_id"])
            processData = {}
            processData["fall_point"] = self.bytes2obj(fall_points)
            processData["court_lines"] = self.bytes2obj(streamData[2])
            processData["court_point_area_id"] = court_point_area_data[1]
            canvas, processedData = self.processDataClient.processAOS(image=last_frame, data=processData)
            
            processedData = self.bytes2obj(processedData)
            receivedData["score"] = processedData["score"]
            receivedData["ball_position_area"] = self.obj2bytes(all_points)
            receivedData["player_position_area"] = self.obj2bytes([])
            receivedData["ball_fall_array"] = fall_points
            
            # SAVE DATA
            self.savePlayingData(receivedData["id"], receivedData)
            
            responseClientData = {}
            responseClientData["fall_point"] = processData["fall_point"]
            responseClientData["score"] = processedData["score"]

            return rc.gameObservationControllerResponse(data=self.obj2bytes(responseClientData), frame=canvas)

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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_mainRouterServerServicer_to_server(MainServer(), server)
    server.add_insecure_port('[::]:50011')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()