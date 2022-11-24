import logging

from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from libs.DefaultChain.BallPositionPredictorChain import BallPositionPredictorChain
from libs.DefaultChain.ConsumerChain import ConsumerChain
from libs.DefaultChain.CourtLineChain import CourtLineChain
from libs.DefaultChain.ITNScoreChain import ITNScoreChain
from libs.DefaultChain.PrepareProcessChain import PrepareProcessChain
from libs.DefaultChain.ProcessAlgorithmChain import ProcessAlgorithmChain
from libs.DefaultChain.SaveResultChain import SaveResultChain

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


MAX_WORKERS = 5
class WorkManager():
    def __init__(self):
        super().__init__()
        
        # Clients
        self.kafkaProducerManager  = KafkaProducerManager()
        self.kafkaConsumerManager = KafkaConsumerManager()
        self.entryPoint = self.SetDefaultChain()
        

    def SetDefaultChain(self):
        entryPoint = PrepareProcessChain()
        entryPoint.SetNext(ConsumerChain()) \
            .SetNext(CourtLineChain()) \
            .SetNext(ProcessAlgorithmChain()) \
            .SetNext(BallPositionPredictorChain()) \
            .SetNext(ITNScoreChain()) \
            .SetNext(SaveResultChain()
            )
        return entryPoint


    #! Main Server
    # Manage Producer----------------------------------------------------------
    def getAllProducerProcesses(self):
        return self.kafkaProducerManager.getAllProducerProcesses()


    def stopProducer(self, process_name):
        return self.kafkaProducerManager.stopProducer(process_name)


    def stopAllProducerProcesses(self):
        return self.kafkaProducerManager.stopAllProducerProcesses()


    # Manage Consumer----------------------------------------------------------
    def getAllConsumers(self, request, context):
        return self.kafkaConsumerManager.getAllConsumers()


    def stopConsumer(self, request, context):
        return self.kafkaConsumerManager.stopConsumer(request.data)


    def stopAllConsumers(self, request, context):
        return self.kafkaConsumerManager.stopAllConsumers()
    

    def ProcessData(self, **kwargs):
        self.entryPoint.Handle(**kwargs)

