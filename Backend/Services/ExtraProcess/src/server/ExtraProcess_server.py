import itertools
import logging
import queue
from concurrent import futures

import conf.ExtraProcess_pb2 as rc
import conf.ExtraProcess_pb2_grpc as rc_grpc
import cv2
import grpc
from client.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from lib.DrawingTools import DrawingTools
from lib.helpers import Converters, EncodeManager, Tools
from lib.PoseConvertTools import PoseConvertTools
from vidgear.gears import CamGear, WriteGear

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)



MAX_MESSAGE_LENGTH = 10*1024*1024
class ExtraProcessServer(rc_grpc.ExtraProcessServicer):
    def __init__(self) -> None:
        super().__init__()
        self.consumerClient = KafkaConsumerManager()
        self.drawingTools = DrawingTools()
        self.poseConvertTools = PoseConvertTools()

    def MergeData(self, request, context):
        process_results = Converters.Bytes2Obj(request.Data)
        # "ball_position_array", "ball_fall_array",
        # "player_position_array", "score", "kafka_topic_name",
        # "body_pose_array", "stream_id", "source", "is_video",
        # "name", court_line_array
        if process_results["kafka_topic_name"] is not None:
            logging.error(f'Topic adı: {process_results["kafka_topic_name"]}')
            FrameIterator = self.consumerClient.consumer(process_results["kafka_topic_name"], f"MergeData_{Tools.GetUID()}")

            frame = None; h = ...; w = ...; c = ...
            # while frame is None:
            #     item = next(FrameIterator)
            #     if item.data is not None:
            #         frame = Converters.Bytes2Frame(item.data)
            #         h, w, c = frame.shape

            # videoWriter = cv2.VideoWriter(f'/MergedVideo/{process_results["name"]}_{process_results["kafka_topic_name"]}.mp4', cv2.VideoWriter_fourcc(*'MJPG'), 60, (w, h))
            output_params = {
                "-input_framerate": 239.76,
                "-codec": "h264_vaapi",
                # "-vaapi_device": "/dev/dri/renderD128",
                # "-vf": "format=nv12,hwupload"
            }
            
            videoWriter = WriteGear(output_filename=f'/MergedVideo/{process_results["kafka_topic_name"]}.mp4',logging=True, **output_params)

            bodyPoseArray = None
            ballPositionArray = None
            ballFallArray = None
            courtLineArray = None
            # Body Bose
            if process_results["body_pose_array"] != "" or process_results["body_pose_array"] is not None:
                bodyPoseArray = EncodeManager.Deserialize(process_results["body_pose_array"])
            
            # Ball Position
            if process_results["ball_position_array"] != "" or process_results["ball_position_array"] is not None:
                ballPositionArray = EncodeManager.Deserialize(process_results["ball_position_array"])
            
            # Ball Fall Coordinate
            if process_results["ball_fall_array"] != "" or process_results["ball_fall_array"] is not None:
                ballFallArray = EncodeManager.Deserialize(process_results["ball_fall_array"])
                ballFallArray = max(ballFallArray, key=lambda i : i[1])

            if process_results["court_line_array"] != "" or process_results["court_line_array"] is not None:
                courtLineArray = EncodeManager.Deserialize(process_results["court_line_array"])

            n = 15
            q = queue.deque()
            [q.appendleft(None) for i in range(0,n)]
            for item, bodyPose, ballPosition in itertools.zip_longest(
                    FrameIterator, 
                    bodyPoseArray if bodyPoseArray is not None else [], 
                    ballPositionArray if ballPositionArray is not None else []
                ):
                frame = Converters.Bytes2Frame(item.data)
                
                if frame is None:
                    continue

                if bodyPose is not None:
                    bodyPose = self.poseConvertTools.Dict2Point(bodyPose)
                    angles = self.drawingTools.GetSpecialAngles(bodyPose)
                    frame = self.drawingTools.DrawAngles(frame, angles, bodyPose)

                if ballPosition is not None:
                    if ballPosition[0] is not None:
                        q.appendleft(ballPosition)
                        q.pop()
                    for i in range(0, n):
                        point = q[i]
                        if point is not None:
                            frame = cv2.circle(frame, (int(point[0]), int(point[1])), 5, (0, 255, 255), 2)

                if ballFallArray is not None:
                    if ballFallArray[0] is not None:
                        frame = cv2.circle(frame, (int(ballFallArray[0]), int(ballFallArray[1])), 5, (255, 255, 255), 2)
                        frame = cv2.circle(frame, (int(ballFallArray[0]), int(ballFallArray[1])), 3, (0, 0, 255), -1)

                if courtLineArray is not None:
                    for item in courtLineArray[0]:
                        if item is not None:
                            if item[0] is not None:
                                logging.warning(item)
                                frame = cv2.line(frame, (int(item[0]), int(item[1])), (int(item[2]), int(item[3])), (0, 255, 0), 2, cv2.LINE_AA)

                frame = cv2.putText(frame,f'Puan: {process_results["score"]}', (30, 30), cv2.FONT_HERSHEY_TRIPLEX, 1, (255,0,255), 1, cv2.LINE_AA)
                videoWriter.write(frame)


            for item in FrameIterator:
                frame = Converters.Bytes2Frame(item.data)
                videoWriter.write(frame)
        
        videoWriter.close()
        # videoWriter.release()
        #! Eğer Topic Yoksa: Orijinal videodan çek

        if process_results["is_video"]:
            ...
        logging.error("İşlem Tamamlandı.")
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




