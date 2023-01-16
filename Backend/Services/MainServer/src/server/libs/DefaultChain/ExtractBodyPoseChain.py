import logging

from clients.BodyPose.BodyPose_client import BodyPoseClient
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


class ExtractBodyPoseChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.bodyPoseClient = BodyPoseClient()


    def Handle(self, **kwargs):
        byte_frame = kwargs.get("byte_frame", None)
        frame = Converters.Bytes2Frame(byte_frame)
        courtLines = kwargs.get("courtLines", None)
        player_position_data = kwargs.get("player_position_data", [])

        
        points, angles, patch_canvas, cropped_frame_bytes = None, None, None, None
        # [[1234.0, 356.0, 1289.0, 498.0, 0.82714844, 0.0], [2216.0, 975.0, 2495.0, 1438.0, 0.93603516, 0.0]]:
        if len(player_position_data)>0 and len(courtLines)>0:
            netLine = courtLines[2]
            firstPlayerPosition = max(player_position_data, key=lambda y: y[1]+y[3])
            firstPlayerPositionCenter = [ (firstPlayerPosition[0] + firstPlayerPosition[2])/2, (firstPlayerPosition[1] + firstPlayerPosition[3])/2 ]
            
            if firstPlayerPositionCenter[1] > netLine[1]-20:
                cropped_frame = frame[ int(firstPlayerPosition[1]-50):int(firstPlayerPosition[3]+50), # x y x y
                                       int(firstPlayerPosition[0]-50):int(firstPlayerPosition[2]+50)
                                    ]
                cropped_frame_bytes = Converters.Frame2Bytes(cropped_frame)

                result = self.bodyPoseClient.ExtractBodyPose(cropped_frame_bytes )
                points, angles, patch_canvas = Converters.Bytes2Obj(result.Data)

        
                if points is not None:
                    if len(points) > 0:
                        for key, value in points.items():
                            for ikey, ivalue in value.items():
                                ivalue[0] += firstPlayerPosition[0]-50
                                ivalue[1] += firstPlayerPosition[1]-50
                                points[key][ikey] = ivalue


        kwargs["body_pose_points"] = points
        kwargs["body_pose_angles"] = angles
        kwargs["body_pose_canvas"] = patch_canvas

        return super().Handle(**kwargs)


