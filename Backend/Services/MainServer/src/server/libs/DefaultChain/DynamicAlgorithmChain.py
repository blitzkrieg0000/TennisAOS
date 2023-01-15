from concurrent import futures
from Backend.Services.MainServer.src.server.libs.DefaultChain.DetectPlayerPositionChain import DetectPlayerPositionChain

from libs.DefaultChain.ExtractBodyPoseChain import ExtractBodyPoseChain
from libs.DefaultChain.handler import AbstractHandler
from libs.DefaultChain.TrackballChain import TrackballChain
from libs.helpers import Converters


class DynamicAlgorithmChain(AbstractHandler):
    def __init__(self, algorithms) -> None:
        super().__init__()
        # Algorithm Chains
        self.algorithmInstances = {}
        self.algorithmInstances["ExtractBodyPoseChain"] = ExtractBodyPoseChain
        self.algorithmInstances["TrackballChain"] = TrackballChain
        self.algorithmInstances["DetectPlayerPositionChain"] = DetectPlayerPositionChain

        # Prepare MultiThreading
        self.ThreadExecutor = futures.ThreadPoolExecutor(max_workers=len(algorithms))
        self.orderedAlgorithmSubmits = self.CreateDynamicProcessChain(self.algorithmSequence)
    

    def CreateSubmit(self, algorithms, kwargs):
        threadSubmits = {
            self.ThreadExecutor.submit(self.algorithmInstances[algorithm](), kwargs) : algorithm for algorithm in algorithms
        }
        return threadSubmits


    def Handle(self, **kwargs):
        frame = kwargs["frame"]
        data = kwargs.get("data", None)

        # PREPARE SUBMIT
        threadSubmits = self.CreateSubmit(frame, data)

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


        return super().Handle(**kwargs)