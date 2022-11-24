from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.ProcessData.pd_client import PDClient
from clients.Redis.redis_client import RedisCacheManager
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters, Repositories


#* C6
class ITNScoreChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.predictFallPositionClient = PFPClient()
        self.processDataClient = PDClient()
        self.redisCacheManager = RedisCacheManager()

    def Handle(self, **kwargs):
        data = kwargs.get("data", None)
        courtLines = kwargs.get("courtLines", None)
        ball_fall_array = kwargs.get("ball_fall_array", None)
        canvasBytes = kwargs.get("canvasBytes", None)
        processAOSRequestData = {}

        court_point_area_data = Repositories.getCourtPointAreaId(self.redisCacheManager, data["aos_type_id"])[0]
        processAOSRequestData["court_lines"] = courtLines
        processAOSRequestData["fall_point"] = ball_fall_array
        processAOSRequestData["court_point_area_id"] = court_point_area_data["court_point_area_id"]
        canvasBytes, processedAOSData = self.processDataClient.processAOS(image=canvasBytes, data=processAOSRequestData)
        processedAOSData = Converters.Bytes2Obj(processedAOSData)

        kwargs["processedAOSData"] = processedAOSData
        kwargs["canvasBytes"] = canvasBytes
        return super().Handle(**kwargs)