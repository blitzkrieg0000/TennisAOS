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
        allData = {}

        if len(data)>0:
            newTopicName = Tools.generateTopicName(data["kafka_topic_name"], 0)
            res = Repositories.saveTopicName(self.rcm, data["stream_id"], newTopicName)

            #! 1-KAFKA_PRODUCER:
            # Streaming başlat
            threadName = self.kpm.startProduce(newTopicName, data["source"], limit=data["limit"])
            
            #! 2-KAFKA_CONSUMER:
            # Streaming oku
            BYTE_FRAMES_GENERATOR = self.kcm.consumer(newTopicName, "consumergroup-balltracker-0", -1, False)

            all_points = []
            processData = {}
            canvas = None
            first_frame = None
            for i, bytes_frame in enumerate(BYTE_FRAMES_GENERATOR):
                if i==0:
                    first_frame = bytes_frame.data
                    courtPoints = None
                    frame = Converters.bytes2frame(bytes_frame.data)
                    if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                        courtPoints = EncodeManager.deserialize(data["court_line_array"])
                    else:
                        courtPoints = self.dclc.extractCourtLines(image=bytes_frame.data)

                        # Tenis çizgilerini postgresqle kaydet
                        if courtPoints is not None:
                            SerializedCourtPoints = EncodeManager.serialize(Converters.bytes2obj(courtPoints))
                            Repositories.saveCourtLinePoints(self.rcm, data["stream_id"], SerializedCourtPoints)
                    frame = Tools.drawLines(frame, courtPoints)
                    processData["court_lines"], canvas = courtPoints, Converters.frame2bytes(frame)

                #! 4-TRACKBALL (DETECTION)
                balldata = self.tbc.findTennisBallPosition(bytes_frame.data, newTopicName) #TopicName Input Array olarak ayarlanmadı, unique olması için düşünüldü!!!
                all_points.append(Converters.bytes2obj(balldata))
                
            if first_frame is None:
                assert "first_frame is None"

            # PREDICT BALL POSITION
            allData["ball_fall_array"] = self.pfpc.predictFallPosition(all_points)
            
            #PROCESS DATA
            court_point_area_data = Repositories.getCourtPointAreaId(self.rcm, data["aos_type_id"])[0]

            processData["fall_point"] = Converters.bytes2obj(allData["ball_fall_array"])
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
