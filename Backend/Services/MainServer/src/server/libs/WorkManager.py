from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from libs.DefaultChain.BallPositionPredictorChain import BallPositionPredictorChain
from libs.DefaultChain.ConsumerChain import ConsumerChain
from libs.DefaultChain.CourtLineChain import CourtLineChain
from libs.DefaultChain.ITNScoreChain import ITNScoreChain
from libs.DefaultChain.PrepareProcessChain import PrepareProcessChain
from libs.DefaultChain.ProcessAlgorithmChain import ProcessAlgorithmChain
from libs.DefaultChain.SaveResultChain import SaveResultChain


MAX_WORKERS = 5
class WorkManager():
    def __init__(self):
        super().__init__()
        
        # Clients
        self.kafkaProducerManager  = KafkaProducerManager()
        self.kafkaConsumerManager = KafkaConsumerManager()
        self.entryPoint = None
        

    def SetVideoChain(self):
        self.entryPoint = PrepareProcessChain()
        self.entryPoint.SetNext(ConsumerChain()) \
            .SetNext(CourtLineChain()) \
            .SetNext(ProcessAlgorithmChain()) \
            .SetNext(BallPositionPredictorChain()) \
            .SetNext(ITNScoreChain()) \
            .SetNext(SaveResultChain())


    def SetStreamChain(self):
        self.entryPoint = ConsumerChain()
        self.entryPoint.SetNext(CourtLineChain()) \
            .SetNext(ProcessAlgorithmChain()) \
            .SetNext(BallPositionPredictorChain()) \
            .SetNext(ITNScoreChain()) \
            .SetNext(SaveResultChain())


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
    

    def ProcessVideoData(self, **kwargs):
        self.SetVideoChain()
        self.entryPoint.Handle(**kwargs)


    def ProcessStreamData(self, **kwargs):
        self.SetStreamChain()
        self.entryPoint.Handle(**kwargs)
