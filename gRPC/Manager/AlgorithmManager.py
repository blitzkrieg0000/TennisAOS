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
from libs.helpers import Converters, Repositories, Tools
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
        streamData = Repositories.getStreamData(self.rcm, data["stream_id"])[0]

        if len(streamData)>0:
            courtPoints = None
            SerializedCourtPoints = None
            newTopicName = Tools.generateTopicName(streamData["stream_name"], 0) # Unique name
            
            # TODO Hata olduğunda servis isteğini sonlandırmak için gerekli hamleleri yap.
            # self.topicGarbageCollector(context, newTopicName)

            #! 2-REDIS:
            # TOPIC ismini kaydet
            res = Repositories.saveTopicName(self.rcm, data["stream_id"], newTopicName)

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
                frame = Converters.bytes2frame(bytes_frame.data)

                if streamData["court_line_array"] is not None and streamData["court_line_array"] != "" and not data["force"]:
                    line_arrays = self.encodeManager.deserialize(streamData["court_line_array"])
                    frame = Tools.drawLines(frame, line_arrays)
                    return line_arrays, Converters.frame2bytes(frame)

                courtPoints = self.dclc.extractCourtLines(image=bytes_frame.data)

            #! 6-REDIS:
            # Tenis çizgilerini postgresqle kaydet
            if courtPoints is not None:
                SerializedCourtPoints = self.encodeManager.serialize(Converters.bytes2obj(courtPoints))
                Repositories.saveCourtLinePoints(self.rcm, data["stream_id"], SerializedCourtPoints)
            
            # DeleteTopic
            self.kpm.deleteTopics([newTopicName])

            frame = Tools.drawLines(frame, courtPoints)
            return courtPoints, Converters.frame2bytes(frame)
        else:
            assert "Stream Data (ID={}) Not Found".format(data["stream_id"])

    def StartGameObservationController(self, data):
        allData = {}

        #! 1-REDIS
        # Stream bilgilerini al
        streamData = Repositories.getStreamData(self.rcm, data["stream_id"])[0]
        
        if len(streamData)>0:

            newTopicName = Tools.generateTopicName(streamData["kafka_topic_name"], 0)
            res = Repositories.saveTopicName(self.rcm, data["stream_id"], newTopicName)

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
                all_points.append(Converters.bytes2obj(balldata))
                last_frame = bytes_frame.data
            
            if last_frame is None:
                assert "last_frame is None"

            # PREDICT BALL POSITION
            fall_points = self.pfpc.predictFallPosition(all_points)
            
            allData["ball_fall_array"] = fall_points

            #PROCESS DATA
            court_point_area_data = Repositories.getCourtPointAreaId(self.rcm, data["aos_type_id"])[0]

            processData = {}
            processData["fall_point"] = Converters.bytes2obj(fall_points)
            processData["court_lines"], canvas = self.detectCourtLinesController(data)
            processData["court_point_area_id"] = court_point_area_data["court_point_area_id"]

            canvas, processedData = self.processDataClient.processAOS(image=canvas, data=processData)
            processedData = Converters.bytes2obj(processedData)

            allData["score"] = processedData["score"]
            allData["ball_position_area"] = Converters.obj2bytes(all_points)
            allData["player_position_area"] = Converters.obj2bytes([])
            allData["stream_id"] = data["stream_id"]
            allData["aos_type_id"] = data["aos_type_id"]
            allData["player_id"] = data["player_id"]
            allData["court_id"] = data["court_id"]

            # SAVE DATA
            Repositories.savePlayingData(self.rcm, allData)
            
            # CreateResponse
            canvas = Converters.bytes2frame(canvas)
            return processData, Converters.frame2base64(canvas)
