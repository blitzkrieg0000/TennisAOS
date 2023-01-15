import numpy as np
from clients.TrackBall.tb_client import TBClient
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters


class TrackballChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.trackBallClient = TBClient()


    def Handle(self, **kwargs):
        court_warp_matrix = kwargs.get("court_warp_matrix", None)
        byte_frame = kwargs.get("byte_frame", None)
        data = kwargs.get("data", None)

        # Request
        balldata = self.trackBallClient.findTennisBallPosition(byte_frame, data["topicName"])
        kwargs["ball_position"] = np.array(Converters.Bytes2Obj(balldata))
        
        return super().Handle(**kwargs)
