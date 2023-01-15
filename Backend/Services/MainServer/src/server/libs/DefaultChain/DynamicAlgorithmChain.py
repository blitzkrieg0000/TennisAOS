from concurrent import futures
from Backend.Services.MainServer.src.server.libs.DefaultChain.DetectPlayerPositionChain import DetectPlayerPositionChain

from libs.DefaultChain.ExtractBodyPoseChain import ExtractBodyPoseChain
from libs.DefaultChain.handler import AbstractHandler
from libs.DefaultChain.TrackballChain import TrackballChain
from libs.helpers import Converters


class DynamicAlgorithmChain(AbstractHandler):
    def __init__(self, algorithms) -> None:
        super().__init__()
        self.algorithms = algorithms
        # Algorithm Chains
        self.algorithmClasses = {}
        self.algorithmClasses["ExtractBodyPoseChain"] = ExtractBodyPoseChain
        self.algorithmClasses["TrackballChain"] = TrackballChain
        self.algorithmClasses["DetectPlayerPositionChain"] = DetectPlayerPositionChain
        
        # Prepare MultiThreading
        self.ThreadExecutor = futures.ThreadPoolExecutor(max_workers=len(algorithms))
    

    def CreateSubmit(self, **kwargs):
        threadSubmits = {
            self.ThreadExecutor.submit(self.algorithmClasses[algorithm](), **kwargs) : algorithm for algorithm in self.algorithms
        }
        return threadSubmits
    

    def ExitCode(self, data):
        self.ThreadExecutor.shutdown()
        self.trackBallClient.deleteDetector(data["topicName"])


    def Handle(self, **kwargs):

        # PREPARE SUBMIT
        threadSubmits = self.CreateSubmit(**kwargs)

        # RUN SUBMITS CONCURENTLY
        threadIterator = futures.as_completed(threadSubmits)

        # WAIT CONCURENT PROCESS
        balldata = None
        points = None
        angles = None
        canvas = None
        
        for future in threadIterator:
            name = threadSubmits[future]
            results = future.result()
            kwargs.update(results)

        return super().Handle(**kwargs)