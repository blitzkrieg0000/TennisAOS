import mainRouterServer_pb2 as rc
from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Postgres.postgres_client import PostgresDatabaseClient
from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from clients.TrackBall.tb_client import TBClient
from libs.helpers import Converters, EncodeManager, Repositories, Tools
from libs.logger import logger


class AlgorithmManager():
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
    def StartGameObservationController(self, data):
        resultData = {}

        if len(data)>0:
            newTopicName = Tools.generateTopicName(data["kafka_topic_name"], 0)
            res = Repositories.saveTopicName(self.rcm, data["stream_id"], newTopicName)

            #! 1-KAFKA_PRODUCER:
            threadName = self.kpm.startProduce(newTopicName, data["source"], limit=data["limit"])
            
            #! 2-KAFKA_CONSUMER:
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newTopicName, "consumergroup-balltracker-0", -1, False)

            all_points = []
            processAOSRequestData = {}
            canvas = None
            first_frame = None

            #! 3-DETECT_COURT_LINES (Extract Tennis Court Lines)
            bytes_frame = next(BYTE_FRAMES_GENERATOR)
            if bytes_frame is not None:
                first_frame = bytes_frame.data
                frame = Converters.bytes2frame(first_frame)
                
                if frame is None:
                    assert "İlk kare doğru alınamadı."

                if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                    processAOSRequestData["court_lines"] = EncodeManager.deserialize(data["court_line_array"])
                else:
                    courtPointsBytes = self.dclc.extractCourtLines(image=first_frame)
                    processAOSRequestData["court_lines"] = Converters.bytes2obj(courtPointsBytes)

                    # Tenis çizgilerini postgresqle kaydet
                    if processAOSRequestData["court_lines"] is not None:
                        SerializedCourtPoints = EncodeManager.serialize(processAOSRequestData["court_lines"])
                        Repositories.saveCourtLinePoints(self.rcm, data["stream_id"], SerializedCourtPoints)
                
                frame = Tools.drawLines(frame, processAOSRequestData["court_lines"])
                canvas = Converters.frame2bytes(frame)
            
            #! 4-TRACKBALL (DETECTION)
            for i, bytes_frame in enumerate(BYTE_FRAMES_GENERATOR):
                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!
                all_points.append(Converters.bytes2obj(balldata))
                
            #! 5-PREDICT_BALL_POSITION
            resultData["ball_fall_array"] = self.pfpc.predictFallPosition(all_points)
            
            #! 6-PROCESS_AOS_DATA
            court_point_area_data = Repositories.getCourtPointAreaId(self.rcm, data["aos_type_id"])[0]
            processAOSRequestData["fall_point"] = Converters.bytes2obj(resultData["ball_fall_array"])
            processAOSRequestData["court_point_area_id"] = court_point_area_data["court_point_area_id"]
            canvas, processedAOSData = self.processDataClient.processAOS(image=canvas, data=processAOSRequestData)
            canvas = Converters.bytes2frame(canvas)
            processedAOSData = Converters.bytes2obj(processedAOSData)

            #! 7-SAVE_PROCESSED_DATA
            resultData["score"] = processedAOSData["score"]
            resultData["ball_position_area"] = Converters.obj2bytes(all_points)
            resultData["player_position_area"] = Converters.obj2bytes([])
            resultData["stream_id"] = data["stream_id"]
            resultData["aos_type_id"] = data["aos_type_id"]
            resultData["player_id"] = data["player_id"]
            resultData["court_id"] = data["court_id"]
            Repositories.savePlayingData(self.rcm, resultData)
            
            # CreateResponse
            return resultData, Converters.frame2base64(canvas)