import logging
from concurrent import futures

import cv2
import numpy as np
from clients.BodyPose.BodyPose_client import BodyPoseClient
from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Postgres.postgres_client import PostgresDatabaseClient
from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from clients.TrackBall.tb_client import TBClient
from libs.helpers import Converters, EncodeManager, Repositories, Tools

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


MAX_WORKERS = 5
class WorkManager():
    def __init__(self):
        super().__init__()
        self.kafkaProducerManager  = KafkaProducerManager()
        self.postgresClient = PostgresDatabaseClient()
        self.redisCacheManager = RedisCacheManager()
        self.detectCourtLineClient = DCLClient()
        self.kafkaConsumerManager = KafkaConsumerManager()
        self.trackBallClient = TBClient()
        self.predictFallPositionClient = PFPClient()
        self.processDataClient = PDClient()
        self.bodyPoseClient = BodyPoseClient()


        # Reference net info
        self.court_warp_matrix = None
        self.court = cv2.cvtColor(cv2.imread('/usr/src/app/src/server/asset/court_reference.png'), cv2.COLOR_BGR2GRAY)
        
        self.court_mask = np.ones_like(self.court)
        self.net = ((286, 1748), (1379, 1748))
        self.white_mask = self.court_mask.copy()
        self.white_mask[:self.net[0][1] - 1000, :] = 0
        self.ThreadExecutor = futures.ThreadPoolExecutor(max_workers=1)


    #! Main Server
    # Manage Producer----------------------------------------------------------
    def getAllProducerProcesses(self):
        return self.kafkaProducerManager.getAllProducerProcesses()

    def stopProducer(self, process_name):
        return self.kafkaProducerManager.stopProducer(process_name)

    def stopAllProducerProcesses(self):
        return self.kafkaProducerManager.stopAllProducerProcesses()


    # Manage Consumer----------------------------------------------------------
    def getAllConsumers(self, request, context):
        return self.kafkaConsumerManager.getAllConsumers()

    def stopConsumer(self, request, context):
        return self.kafkaConsumerManager.stopConsumer(request.data)

    def stopAllConsumers(self, request, context):
        return self.kafkaConsumerManager.stopAllConsumers()
    

    # Algorithms---------------------------------------------------------------
    def Prepare(self, data, independent=False, errorLimit=3):
        newTopicName = Tools.generateTopicName(data["stream_name"], 0)
        res = Repositories.saveTopicName(self.redisCacheManager, data["process_id"], newTopicName)
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
        send_queue, empty_message, responseIterator = self.kafkaProducerManager.producer(**arr)

        return data, send_queue, empty_message, responseIterator


    def ProducerController(self, data):
        all_points = []
        all_body_pose_points = []
        resultData = {}
        processAOSRequestData = {}
        canvas = None
        canvasBytes = None
        first_frame_bytes = None
        courtLines = None

        #! 2-KAFKA_CONSUMER:
        BYTE_FRAMES_GENERATOR = self.kafkaConsumerManager.consumer(data["topicName"], "consumergroup-balltracker-0", -1)

        #! 3-DETECT_COURT_LINES (Extract Tennis Court Lines)
        #İlk frame i al ve saha tespiti yapılmamışsa yap
        consumerResponse = next(BYTE_FRAMES_GENERATOR)

        if consumerResponse is not None:
            first_frame_bytes = consumerResponse.data
            frame = Converters.Bytes2Frame(first_frame_bytes)
            
            if frame is None:
                assert "İlk kare doğru alınamadı."
            
            # Override -> Session video ise her videonun ayrı kaynağı olacağından, varsayılan değerlere override yap.
            overrideData = Repositories.getCourtLineBySessionId(self.redisCacheManager, data["session_id"])[0]
            try:
                data["court_line_array"] = overrideData["st_court_line_array"]
                data["sp_stream_id"] = overrideData["sp_stream_id"]
            except Exception as e:
                logging.warning(e)

            if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                courtLines, self.court_warp_matrix = EncodeManager.deserialize(data["court_line_array"])
            
            else:
                courtPointsBytes = b""
                try:
                    courtPointsBytes = self.detectCourtLineClient.extractCourtLines(image=first_frame_bytes)
                except:
                    Repositories.markAsCompleted(self.redisCacheManager, data["process_id"])
                    return None

                courtLines, self.court_warp_matrix = Converters.Bytes2Obj(courtPointsBytes)


            # Tenis çizgilerini postgresqle kaydet
            if courtLines is not None:
                SerializedCourtPoints = EncodeManager.serialize(np.array([courtLines, self.court_warp_matrix]))
                data["court_line_array"] = SerializedCourtPoints
                Repositories.saveCourtLinePoints(self.redisCacheManager, data["stream_id"], data["session_id"], SerializedCourtPoints)
            else:
                return None

                
            canvas = Tools.drawLines(frame, courtLines)
            canvasBytes = Converters.Frame2Bytes(canvas)

        #! 4-ALGORITHMS (DETECTION)
        for i, consumerResponse in enumerate(BYTE_FRAMES_GENERATOR):
            
            temp_frame  = Converters.Bytes2Frame(consumerResponse.data)
            mask = cv2.warpPerspective(self.white_mask, np.array(self.court_warp_matrix), temp_frame.shape[1::-1])
            temp_frame[mask == 0, :] = (0, 0, 0)
            
            cv2.imwrite("/temp/temp.jpg", temp_frame)

            threadSubmits = {
                self.ThreadExecutor.submit(self.trackBallClient.findTennisBallPosition, consumerResponse.data, data["topicName"]) : "DetectBall",
                self.ThreadExecutor.submit(self.bodyPoseClient.ExtractBodyPose, Converters.Frame2Bytes(temp_frame)) : "BodyPose"
            }

            threadIterator = futures.as_completed(threadSubmits)

            for future in threadIterator:
                result = future.result()
                name = threadSubmits[future]
                if name == "DetectBall":
                    balldata = result
                elif name == "BodyPose":
                    points, angles, canvas = Converters.Bytes2Obj(result.Data)
            
            logging.error(f"{points} - {angles}")


            all_body_pose_points.append(np.array(points))
            all_points.append(np.array(Converters.Bytes2Obj(balldata)))
        
        self.ThreadExecutor.shutdown()
        self.trackBallClient.deleteDetector(data["topicName"])
        
        #! 5-PREDICT_BALL_POSITION
        ball_fall_array_bytes = self.predictFallPositionClient.predictFallPosition(all_points)
        ball_fall_array = Converters.Bytes2Obj(ball_fall_array_bytes)

        #! 6-PROCESS_AOS_DATA
        court_point_area_data = Repositories.getCourtPointAreaId(self.redisCacheManager, data["aos_type_id"])[0]
        processAOSRequestData["court_lines"] = courtLines
        processAOSRequestData["fall_point"] = ball_fall_array
        processAOSRequestData["court_point_area_id"] = court_point_area_data["court_point_area_id"]
        canvasBytes, processedAOSData = self.processDataClient.processAOS(image=canvasBytes, data=processAOSRequestData)
        processedAOSData = Converters.Bytes2Obj(processedAOSData)
        
        # Draw Fall Points
        canvas = Converters.Bytes2Frame(canvasBytes)
        canvas = Tools.drawCircles(canvas, ball_fall_array)
        
        #! 7-SAVE_PROCESSED_DATA
        resultData["ball_position_array"] = EncodeManager.serialize(np.array(all_points))
        resultData["body_pose_array"] = EncodeManager.serialize(np.array(all_body_pose_points))
        resultData["player_position_array"] = EncodeManager.serialize([])
        resultData["ball_fall_array"] = EncodeManager.serialize(ball_fall_array)
        resultData["canvas"] = Converters.Frame2Base64(canvas) 
        resultData["score"] = processedAOSData["score"]
        resultData["process_id"] = data["process_id"]
        resultData["court_line_array"] = data["court_line_array"]
        resultData["stream_id"] = data["stream_id"]
        resultData["aos_type_id"] = data["aos_type_id"]
        resultData["player_id"] = data["player_id"]
        resultData["court_id"] = data["court_id"]
        resultData["description"] = "Bilgi Verilmedi."
        
        Repositories.saveProcessData(self.redisCacheManager, resultData)
        #Repositories.savePlayingData(self.redisCacheManager, resultData)

        Repositories.markAsCompleted(self.redisCacheManager, resultData["process_id"])
