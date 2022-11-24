import numpy as np
from clients.Redis.redis_client import RedisCacheManager
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters, EncodeManager, Repositories, Tools

#* C7
class SaveResultChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redisCacheManager = RedisCacheManager()


    def SaveResults(self, data, processedAOSData, canvas, ball_fall_array, all_body_pose_points, all_ball_positions):
        resultData = {}
        resultData["ball_position_array"] = EncodeManager.serialize(np.array(all_ball_positions))
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
        return resultData


    def Handle(self, **kwargs):

        ball_fall_array = kwargs.get("ball_fall_array", None)
        data = kwargs.get("data", None)
        processedAOSData = kwargs.get("processedAOSData", None)
        all_body_pose_points = kwargs.get("all_body_pose_points", None)
        all_ball_positions = kwargs.get("all_ball_positions", None)
        canvasBytes = kwargs.get("canvasBytes", None)

        # Topun düştüğü yeri işaretle
        canvas = Converters.Bytes2Frame(canvasBytes)
        canvas = Tools.drawCircles(canvas, ball_fall_array)
        
        #! 7-SAVE_PROCESSED_DATA
        resultData = self.SaveResults(data, processedAOSData, canvas, ball_fall_array, all_body_pose_points, all_ball_positions)

        # Processi tamamlandı olarak işaretle
        Repositories.markAsCompleted(self.redisCacheManager, resultData["process_id"])



        return super().Handle(**kwargs)