import logging

from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Producer.producer_client import KafkaProducerManager
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Repositories, Tools

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


#* C1
class PrepareProcessChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.kafkaProducerManager  = KafkaProducerManager()
        self.redisCacheManager = RedisCacheManager()
        self.counter = 0
        
    def Handle(self, **kwargs):
        data = kwargs.get("data", None)
        errorLimit = kwargs.get("errorLimit", 3)
        independent = kwargs.get("independent", False)

        newTopicName = Tools.generateTopicName(data["stream_name"], 0)
        res = Repositories.saveTopicName(self.redisCacheManager, data["process_id"], newTopicName)

        kwargs["data"]["topicName"] = newTopicName

        arr = {
            "topicName" : data["topicName"],
            "source" : data["source"],           #rtmp://192.168.1.100/live
            "isVideo" : data["is_video"],
            "limit": data["limit"],
            "errorLimit" : errorLimit,
            "independent" : independent
        }
        
        send_queue, empty_message, responseIterator = self.kafkaProducerManager.producer(**arr)

        
        kwargs["send_queue"] = send_queue
        kwargs["empty_message"] = empty_message
        kwargs["responseIterator"] = responseIterator

        return super().Handle(**kwargs)