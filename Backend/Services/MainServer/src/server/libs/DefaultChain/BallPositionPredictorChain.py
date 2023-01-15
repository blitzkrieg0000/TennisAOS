from clients.PredictFallPosition.predictFallPosition_client import PFPClient
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.TrackBall.tb_client import TBClient
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters

#* C5
class BallPositionPredictorChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.predictFallPositionClient = PFPClient()
    

    def Handle(self, **kwargs):
        all_ball_positions = kwargs.get("all_ball_positions", None)

        ball_fall_array_bytes = self.predictFallPositionClient.predictFallPosition(all_ball_positions)
        ball_fall_array = Converters.Bytes2Obj(ball_fall_array_bytes)
        
        kwargs["ball_fall_array"] = ball_fall_array
        return super().Handle(**kwargs)