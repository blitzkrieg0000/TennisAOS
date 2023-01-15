from libs.helpers import Converters
from clients.DetectPlayer.PlayerDetector_client import PlayerDetectorClient
from libs.DefaultChain.handler import AbstractHandler


class DetectPlayerPositionChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.detectPlayerClient = PlayerDetectorClient()


    def Handle(self, **kwargs):
        byte_frame = kwargs.get("byte_frame", None)
        frame = Converters.Bytes2Frame(byte_frame)
        
        response = self.detectPlayerClient.Detect(frame)
        player_position_data = Converters.Bytes2Obj(response.Response.Data)
        kwargs["player_position_data"] = player_position_data

        return super().Handle(**kwargs)
