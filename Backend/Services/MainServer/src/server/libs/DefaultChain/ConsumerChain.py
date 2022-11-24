from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.TrackBall.tb_client import TBClient
from libs.DefaultChain.handler import AbstractHandler

#* C2
class ConsumerChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.kafkaConsumerManager = KafkaConsumerManager()
        self.trackBallClient = TBClient()

    
    def Handle(self, **kwargs):
        data = kwargs.get("data", None)

        #! 2-KAFKA_CONSUMER:
        BYTE_FRAMES_GENERATOR = self.kafkaConsumerManager.consumer(data["topicName"], "consumergroup-balltracker-0", -1)
        kwargs["BYTE_FRAMES_GENERATOR"] = BYTE_FRAMES_GENERATOR
        return super().Handle(**kwargs)