import collections
import logging

import numpy as np
from libs.DefaultChain.DynamicAlgorithmChain import DynamicAlgorithmChain
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


#* C4
class AlgorithmChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        algorithms : dict[str, list[str]] = {
            "TrackballChain" : None,
            "ExtractBodyPoseChain" : ["DetectPlayerPositionChain"],
            "DetectPlayerPositionChain" : None
        }
        self.algorithmSequence = self.SortAlgorithmSequence(algorithms)


    def SortAlgorithmSequence(self, Algorithms: dict[str, list[str]]):
        """
            Bağımlılıklara göre algoritmaları sıralar
        """
        AlgorithmChainSequence = []
        PlacedAlgorithms = []
        UnplacedAlgorithms = Algorithms.copy()
        for key, value in Algorithms.items():
            if value is None:
                PlacedAlgorithms.append(key)
                UnplacedAlgorithms.pop(key)

        AlgorithmChainSequence.append(PlacedAlgorithms.copy())

        for _ in range(len(UnplacedAlgorithms)):
            selected = []
            for key, dependencies in UnplacedAlgorithms.items():
                if all([dependecy in PlacedAlgorithms for dependecy in dependencies]):
                    selected.append(key)

            [(UnplacedAlgorithms.pop(skey), PlacedAlgorithms.append(skey)) for skey in selected]
            if len(selected) > 0:
                AlgorithmChainSequence.append(selected)
    
        return AlgorithmChainSequence


    def CreateDynamicAlgorithmChain(self):
        newChain = None
        for chain in self.algorithmSequence:
            chain = DynamicAlgorithmChain(chain)
            if newChain is None:
                newChain = chain
            else:
                newChain.SetNext(chain)

        return newChain


    def Handle(self, **kwargs):
        byte_frame = kwargs.get("byte_frame", None)
        data = kwargs.get("data", None)

        all_ball_positions = []
        all_body_pose_points = []
        createdAlgorithmChain = self.CreateDynamicAlgorithmChain()

        BYTE_FRAMES_GENERATOR = kwargs.get("BYTE_FRAMES_GENERATOR", None)
        
        #! 4-ALGORITHMS
        logging.info("Görüntüler Algoritmalara Dağıtılıyor...")
        for i, consumerResponse in enumerate(BYTE_FRAMES_GENERATOR):
            
            if consumerResponse.data is None or consumerResponse.data == b"":
                continue

            kwargs["frame"] = consumerResponse.data
            kwargs = createdAlgorithmChain.Handle(**kwargs)

            ball_position = kwargs["ball_position"]
            body_pose_points = kwargs["body_pose_points"]
            all_body_pose_points.append(body_pose_points)
            all_ball_positions.append(ball_position)
        logging.info("Algoritmalar Görüntüleri İşledi...")


        # GC
        # TODO Chainler için EXIT kodu tasarla
        # self.ThreadExecutor.shutdown()
        # self.trackBallClient.deleteDetector(data["topicName"])

        kwargs["all_body_pose_points"] = all_body_pose_points
        kwargs["all_ball_positions"] = all_ball_positions
        
        return super().Handle(**kwargs)



