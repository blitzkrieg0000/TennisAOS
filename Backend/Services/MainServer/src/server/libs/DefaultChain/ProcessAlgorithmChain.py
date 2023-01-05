import logging
from concurrent import futures

import cv2
import numpy as np
from clients.BodyPose.BodyPose_client import BodyPoseClient
from clients.TrackBall.tb_client import TBClient
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

#* C4
class ProcessAlgorithmChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.ThreadExecutor = None
        self.trackBallClient = TBClient()
        self.bodyPoseClient = BodyPoseClient()


    def PrepareAlgorithms(self, byte_frame, data):
        threadSubmits = {
            self.ThreadExecutor.submit(self.trackBallClient.findTennisBallPosition, byte_frame, data["topicName"]) : "DetectBall",
            self.ThreadExecutor.submit(self.bodyPoseClient.ExtractBodyPose, byte_frame) : "BodyPose"
        }

        return threadSubmits


    def Handle(self, **kwargs):
        court_warp_matrix = kwargs.get("court_warp_matrix", None)
        byte_frame = kwargs.get("byte_frame", None)
        data = kwargs.get("data", None)

        all_ball_positions = []
        all_body_pose_points = []
        data = kwargs.get("data", None)
        BYTE_FRAMES_GENERATOR = kwargs.get("BYTE_FRAMES_GENERATOR", None)
        
        # PREPARE PoolExecuter
        self.ThreadExecutor = futures.ThreadPoolExecutor(max_workers=2)
       
        #! 4-ALGORITHMS
        logging.info("Görüntüler Algoritmalara Dağıtılıyor...")
        for i, consumerResponse in enumerate(BYTE_FRAMES_GENERATOR):
            
            if consumerResponse.data is None or consumerResponse.data == b"":
                continue

            # PREPARE SUBMIT
            threadSubmits = self.PrepareAlgorithms(consumerResponse.data, data)

            # RUN SUBMITS CONCURENTLY
            threadIterator = futures.as_completed(threadSubmits)

            # WAIT CONCURENT PROCESS
            balldata = None
            points = None
            angles = None
            canvas = None
            
            for future in threadIterator:
                result = future.result()
                name = threadSubmits[future]

                #TODO Hmmm
                if name == "DetectBall":
                    balldata = result
                elif name == "BodyPose":
                    points, angles, canvas = Converters.Bytes2Obj(result.Data)
                    cv2.imwrite("/temp/body.jpg", canvas)

            all_body_pose_points.append(np.array(points))
            all_ball_positions.append(np.array(Converters.Bytes2Obj(balldata)))
        logging.info("Algoritmalar Görüntüleri İşledi...")

        # GC
        self.ThreadExecutor.shutdown()
        self.trackBallClient.deleteDetector(data["topicName"])

        kwargs["all_body_pose_points"] = all_body_pose_points
        kwargs["all_ball_positions"] = all_ball_positions
        
        return super().Handle(**kwargs)