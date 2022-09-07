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
from libs.helpers import Converters, EncodeManager, Repositories, Tools


class WorkManager():
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
    def getAllProducerProcesses(self):
        return self.kpm.getAllProducerProcesses()

    def stopProducer(self, process_name):
        return self.kpm.stopProducer(process_name)

    def stopAllProducerProcesses(self):
        return self.kpm.stopAllProducerProcesses()

    # Manage Consumer----------------------------------------------------------
    #? CONSUMER DÜZENLENİYOR...
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
        all_points = []
        processAOSRequestData = {}
        canvas = None
        first_frame = None
        courtLines = None

        if len(data)>0:
            newTopicName = Tools.generateTopicName(data["stream_name"], 0)
            res = Repositories.saveTopicName(self.rcm, data["stream_id"], newTopicName)

            #! 1-KAFKA_PRODUCER:
            data["newTopicName"] = newTopicName
            threadName = self.kpm.producer(EncodeManager.serialize(data))
            
            #! 2-KAFKA_CONSUMER:
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newTopicName, "consumergroup-balltracker-0", -1, False)

            #! 3-DETECT_COURT_LINES (Extract Tennis Court Lines)
            bytes_frame = next(BYTE_FRAMES_GENERATOR)
            if bytes_frame is not None:
                first_frame = bytes_frame.data
                frame = Converters.bytes2frame(first_frame)
                
                if frame is None:
                    assert "İlk kare doğru alınamadı."

                if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                    courtLines = EncodeManager.deserialize(data["court_line_array"])
                else:
                    courtPointsBytes = self.dclc.extractCourtLines(image=first_frame)
                    courtLines = Converters.bytes2obj(courtPointsBytes)

                    # Tenis çizgilerini postgresqle kaydet
                    if courtLines is not None:
                        SerializedCourtPoints = EncodeManager.serialize(courtLines)
                        data["court_line_array"] = SerializedCourtPoints
                        Repositories.saveCourtLinePoints(self.rcm, data["stream_id"], SerializedCourtPoints)
                
                frame = Tools.drawLines(frame, courtLines)
                canvas = Converters.frame2bytes(frame)
            
            #! 4-TRACKBALL (DETECTION)
            for i, bytes_frame in enumerate(BYTE_FRAMES_GENERATOR):
                # TODO Diğer algoritmalar için concurency.future ile aynı frame kullanılarak işlem yapılacak 
                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!
                all_points.append(np.array(Converters.bytes2obj(balldata)))
                
            #! 5-PREDICT_BALL_POSITION
            ball_fall_array = self.pfpc.predictFallPosition(all_points)
            
            #! 6-PROCESS_AOS_DATA
            court_point_area_data = Repositories.getCourtPointAreaId(self.rcm, data["aos_type_id"])[0]
            processAOSRequestData["court_lines"] = courtLines
            processAOSRequestData["fall_point"] = Converters.bytes2obj(ball_fall_array)
            processAOSRequestData["court_point_area_id"] = court_point_area_data["court_point_area_id"]
            canvasBytes, processedAOSData = self.processDataClient.processAOS(image=canvas, data=processAOSRequestData)
            processedAOSData = Converters.bytes2obj(processedAOSData)

            #! 7-SAVE_PROCESSED_DATA
            resultData["ball_position_array"] = EncodeManager.serialize(np.array(all_points))
            resultData["player_position_array"] = EncodeManager.serialize([])
            resultData["ball_fall_array"] = EncodeManager.serialize(Converters.bytes2obj(ball_fall_array))
            resultData["canvas"] = Converters.frame2base64(Converters.bytes2frame(canvasBytes)) 
            resultData["score"] = processedAOSData["score"]
            resultData["process_id"] = data["process_id"]
            resultData["court_line_array"] = data["court_line_array"]
            resultData["stream_id"] = data["stream_id"]
            resultData["aos_type_id"] = data["aos_type_id"]
            resultData["player_id"] = data["player_id"]
            resultData["court_id"] = data["court_id"]
            resultData["description"] = "Bilgi Verilmedi."
            

            Repositories.saveProcessData(self.rcm, resultData)
            Repositories.savePlayingData(self.rcm, resultData)
            
            # CreateResponse
            return resultData
