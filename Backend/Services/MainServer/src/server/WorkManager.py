import numpy as np

from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Postgres.postgres_client import PostgresDatabaseClient
from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from clients.TrackBall.tb_client import TBClient
from libs.helpers import Converters, EncodeManager, Repositories, Tools


MAX_WORKERS = 5
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
    def getAllConsumers(self, request, context):
        return self.kcm.getAllConsumers()

    def stopConsumer(self, request, context):
        return self.kcm.stopConsumer(request.data)

    def stopAllConsumers(self, request, context):
        return self.kcm.stopAllConsumers()
        

    # Algorithms--------------------------------------------------------------- 
    def Prepare(self, data, independent=False, errorLimit=3):
        newTopicName = Tools.generateTopicName(data["stream_name"], 0)
        res = Repositories.saveTopicName(self.rcm, data["process_id"], newTopicName)
        data["topicName"] = newTopicName

        arr = {
            "topicName" : data["topicName"],
            "source" : data["source"],           #rtmp://192.168.1.100/live
            "isVideo" : data["is_video"],
            "limit": data["limit"],
            "errorLimit" : errorLimit,
            "independent" : independent
        }

        #! 1-KAFKA_PRODUCER:
        send_queue, empty_message, responseIterator = self.kpm.producer(**arr)

        return data, send_queue, empty_message, responseIterator


    def ProducerController(self, data):
        resultData = {}
        all_points = []
        processAOSRequestData = {}
        canvas = None
        canvasBytes = None
        first_frame = None
        courtLines = None

        #! 2-KAFKA_CONSUMER:
        BYTE_FRAMES_GENERATOR = self.kcm.consumer(data["topicName"], "consumergroup-balltracker-0", -1)

        #! 3-DETECT_COURT_LINES (Extract Tennis Court Lines)
        
        bytes_frame = next(BYTE_FRAMES_GENERATOR)

        if bytes_frame is not None:
            first_frame = bytes_frame.data
            frame = Converters.bytes2frame(first_frame)
            
            if frame is None:
                assert "İlk kare doğru alınamadı."
            
            # Override
            overrideData = Repositories.getStreamCourtLineBySessionId(self.rcm, data["session_id"])[0]
            
            try:
                data["court_line_array"] = overrideData["st_court_line_array"]
                data["sp_stream_id"] = overrideData["sp_stream_id"]
            except Exception as e:
                print(e)

            if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                courtLines = EncodeManager.deserialize(data["court_line_array"])
            else:
                courtPointsBytes = b""
                try:
                    courtPointsBytes = self.dclc.extractCourtLines(image=first_frame)
                except:
                    Repositories.markAsCompleted(self.rcm, data["process_id"])
                    return None

                courtLines = Converters.bytes2obj(courtPointsBytes)

            # Tenis çizgilerini postgresqle kaydet
            if courtLines is not None:
                SerializedCourtPoints = EncodeManager.serialize(courtLines)
                data["court_line_array"] = SerializedCourtPoints
                Repositories.saveCourtLinePoints(self.rcm, data["stream_id"], data["session_id"], SerializedCourtPoints)
            
            canvas = Tools.drawLines(frame, courtLines)
            canvasBytes = Converters.frame2bytes(canvas)
        
        #! 4-TRACKBALL (DETECTION)
        for i, bytes_frame in enumerate(BYTE_FRAMES_GENERATOR):
            
            # TODO Diğer algoritmalar için concurency.future ile aynı frame kullanılarak işlem yapılacak 
            balldata = self.tbc.findTennisBallPosition(bytes_frame.data, data["topicName"]) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!
            
            # TODO SAHA ÇİZGİ TAKİBİ
            # TODO OYUNCU BULMA VEYA OYUNCU BULMA+TAKİP

            all_points.append(np.array(Converters.bytes2obj(balldata)))
        self.tbc.deleteDetector(data["topicName"])
        
        #! 5-PREDICT_BALL_POSITION
        ball_fall_array_bytes = self.pfpc.predictFallPosition(all_points)
        ball_fall_array = Converters.bytes2obj(ball_fall_array_bytes)

        #! 6-PROCESS_AOS_DATA
        court_point_area_data = Repositories.getCourtPointAreaId(self.rcm, data["aos_type_id"])[0]
        processAOSRequestData["court_lines"] = courtLines
        processAOSRequestData["fall_point"] = ball_fall_array
        processAOSRequestData["court_point_area_id"] = court_point_area_data["court_point_area_id"]
        canvasBytes, processedAOSData = self.processDataClient.processAOS(image=canvasBytes, data=processAOSRequestData)
        processedAOSData = Converters.bytes2obj(processedAOSData)
        
        # Draw Fall Points
        canvas = Converters.bytes2frame(canvasBytes)
        canvas = Tools.drawCircles(canvas, ball_fall_array)
        
        #! 7-SAVE_PROCESSED_DATA
        resultData["ball_position_array"] = EncodeManager.serialize(np.array(all_points))
        resultData["player_position_array"] = EncodeManager.serialize([])
        resultData["ball_fall_array"] = EncodeManager.serialize(ball_fall_array)
        resultData["canvas"] = Converters.frame2base64(canvas) 
        resultData["score"] = processedAOSData["score"]
        resultData["process_id"] = data["process_id"]
        resultData["court_line_array"] = data["court_line_array"]
        resultData["stream_id"] = data["stream_id"]
        resultData["aos_type_id"] = data["aos_type_id"]
        resultData["player_id"] = data["player_id"]
        resultData["court_id"] = data["court_id"]
        resultData["description"] = "Bilgi Verilmedi."
        
        Repositories.saveProcessData(self.rcm, resultData)
        #Repositories.savePlayingData(self.rcm, resultData)

        Repositories.markAsCompleted(self.rcm, resultData["process_id"])
