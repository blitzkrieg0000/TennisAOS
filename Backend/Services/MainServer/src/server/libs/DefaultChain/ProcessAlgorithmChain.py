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
        self.court = cv2.cvtColor(cv2.imread('/usr/src/app/src/server/asset/court_reference.png'), cv2.COLOR_BGR2GRAY)
        self.court_mask = np.ones_like(self.court)
        self.net = ((286, 1748), (1379, 1748))
        self.white_mask = self.court_mask.copy()
        self.white_mask[:self.net[0][1] - 1000, :] = 0


    def CropBottomCourt(self, byte_frame, court_warp_matrix):
        tempFrame  = Converters.Bytes2Frame(byte_frame)
        mask = cv2.warpPerspective(self.white_mask, np.array(court_warp_matrix), tempFrame.shape[1::-1])
        tempFrame[mask == 0, :] = (0, 0, 0)
        # cv2.imwrite("/temp/temp.jpg", tempFrame)
        return tempFrame


    def PrepareAlgorithms(self, byte_frame, croppedBottomCourtFrame, data):
        threadSubmits = {
            self.ThreadExecutor.submit(self.trackBallClient.findTennisBallPosition, byte_frame, data["topicName"]) : "DetectBall",
            self.ThreadExecutor.submit(self.bodyPoseClient.ExtractBodyPose, Converters.Frame2Bytes(croppedBottomCourtFrame)) : "BodyPose"
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
            
            #PreRequest
            croppedBottomCourtFrame = self.CropBottomCourt(consumerResponse.data, court_warp_matrix)

            # PREPARE SUBMIT
            threadSubmits = self.PrepareAlgorithms(consumerResponse.data, croppedBottomCourtFrame, data)

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

            all_body_pose_points.append(np.array(points))
            all_ball_positions.append(np.array(Converters.Bytes2Obj(balldata)))
        logging.info("Algoritmalar Görüntüleri İşledi...")

        # GC
        self.ThreadExecutor.shutdown()
        self.trackBallClient.deleteDetector(data["topicName"])

        kwargs["all_body_pose_points"] = all_body_pose_points
        kwargs["all_ball_positions"] = all_ball_positions
        
        return super().Handle(**kwargs)