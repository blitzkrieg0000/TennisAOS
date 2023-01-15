from clients.BodyPose.BodyPose_client import BodyPoseClient
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters



class ExtractBodyPoseChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.bodyPoseClient = BodyPoseClient()


    def Handle(self, **kwargs):
        byte_frame = kwargs.get("byte_frame", None)
        
        points, angles, canvas = None, None, None
        result = self.bodyPoseClient.ExtractBodyPose(byte_frame)
        points, angles, canvas = Converters.Bytes2Obj(result.Data)

        kwargs["body_pose_points"] = points
        kwargs["body_pose_angles"] = angles
        kwargs["body_pose_canvas"] = canvas

        return super().Handle(**kwargs)
