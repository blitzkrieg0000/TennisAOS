import logging
from concurrent import futures

from libs.DefaultChain.DetectPlayerPositionChain import \
    DetectPlayerPositionChain
from libs.DefaultChain.ExtractBodyPoseChain import ExtractBodyPoseChain
from libs.DefaultChain.handler import AbstractHandler
from libs.DefaultChain.TrackballChain import TrackballChain

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


class DynamicAlgorithmChain(AbstractHandler):
    def __init__(self, algorithms):
        super().__init__()
        self.algorithms = algorithms
        
        # Algorithm Chains
        self.algorithmClasses = {}
        self.algorithmClasses["ExtractBodyPoseChain"] = ExtractBodyPoseChain
        self.algorithmClasses["TrackballChain"] = TrackballChain
        self.algorithmClasses["DetectPlayerPositionChain"] = DetectPlayerPositionChain
        
        self.algorithmInstances = {}
        
        # Prepare MultiThreading
        logging.info(f"Initiated: {algorithms}")
        self.ThreadExecutor = futures.ThreadPoolExecutor(max_workers=len(algorithms))
        self.CreateInstances()


    def CreateInstances(self):
        self.algorithmInstances = {
            algorithm : self.algorithmClasses[algorithm]() for algorithm in self.algorithms
        }

    # Algoritmalar chain yapısıyla yazıldı fakat chain olarak kullanılmıyor. 
    #Bu sadece ileri ki bir zamanda algoritmaları herhangi bir yerde kullanma ihtiyacı duyulursa diye planlandı.
    #Bu class, aynı anda çalışması gereken algoritmaların "AlgorithmChain" den yönetilmesini sağlıyor.
    # Herhangi bir algoritmanın Handle metoduna tüm argümanlar geçiyor. Böylece sadece gerekli olan argümanları algoritma kullanıyor.
    def CreateSubmit(self, **kwargs):
        threadSubmits = {
            self.ThreadExecutor.submit(self.algorithmInstances[algorithm].Handle, **kwargs) : algorithm for algorithm in self.algorithms
        }
        return threadSubmits
    

    def ExitCode(self, data):
        self.ThreadExecutor.shutdown()

        #TODO: Sadece trackball clienti için bu satır yazılacak: ContextManager ile
        self.trackBallClient.deleteDetector(data["topicName"])


    def Handle(self, **kwargs):
        # PREPARE SUBMIT
        threadSubmits = self.CreateSubmit(**kwargs)

        # RUN SUBMITS CONCURENTLY
        threadIterator = futures.as_completed(threadSubmits)

        # WAIT CONCURENT PROCESS
        for future in threadIterator:
            name = threadSubmits[future]
            results = future.result()
            kwargs.update(results)

        return super().Handle(**kwargs)


