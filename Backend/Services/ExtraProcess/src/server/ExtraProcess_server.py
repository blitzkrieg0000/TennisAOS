from concurrent import futures
import logging
from lib.helpers import Converters, Tools
import conf.ExtraProcess_pb2 as rc
import conf.ExtraProcess_pb2_grpc as rc_grpc
import grpc
from client.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
import cv2

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


MAX_MESSAGE_LENGTH = 10*1024*1024

class ExtraProcessServer(rc_grpc.ExtraProcessServicer):
    def __init__(self) -> None:
        super().__init__()
        self.consumerClient = KafkaConsumerManager()


    def MergeData(self, request, context):
        process_results = Converters.Bytes2Obj(request.Data)

        # "ball_position_array", "ball_fall_array",
        # "player_position_array", "score", "kafka_topic_name",
        # "body_pose_array", "stream_id", "source", "is_video",
        # "name"
        if process_results["kafka_topic_name"] is not None:
            logging.error(f'Topic adı: {process_results["kafka_topic_name"]}')
            FrameIterator = self.consumerClient.consumer(process_results["kafka_topic_name"], f"MergeData_{Tools.GetUID()}")

            if FrameIterator is None:
                ...

            frame = None; h = ...; w = ...; c = ...
            while frame is None:
                item = next(FrameIterator)
                if item.data is not None:
                    frame = Converters.Bytes2Frame(item.data)
                    h, w, c = frame.shape

            logging.error(f'/MergedVideo/{process_results["name"]}_{process_results["kafka_topic_name"]}.mp4{w},{c}')
            videoWriter = cv2.VideoWriter(f'/MergedVideo/{process_results["name"]}_{process_results["kafka_topic_name"]}.mp4', cv2.VideoWriter_fourcc(*'MJPG'), 60, (w, h))
            
            for item in FrameIterator:
                frame = Converters.Bytes2Frame(item.data)
                
                if frame is None:
                    continue
                    
                videoWriter.write(frame)
                #TODO Frame i işle...

            videoWriter.release()

        #! Eğer Topic Yoksa: Orijinal videodan çek
        if process_results["is_video"]:
            ...

        return rc.ExtraProcessResponse(Message="")



def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
        ],
        # compression=grpc.Compression.Gzip
    )

    rc_grpc.add_ExtraProcessServicer_to_server(ExtraProcessServer(), server)
    server.add_insecure_port('[::]:50071')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()




