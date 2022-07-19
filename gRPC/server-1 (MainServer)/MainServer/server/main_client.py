from __future__ import print_function

import pickle
import grpc
import mainRouterServer_pb2 as rc
import mainRouterServer_pb2_grpc as rc_grpc
from libs.logger import logger


class MainClient():
    def __init__(self):
        self.channel = grpc.insecure_channel("localhost:50011") #MAIN-SERVICE-DEPLOYMENT-IP TODO: NODEPORT İLE DIŞARI AÇILACAK TEK BİR DEPLOYMENTA BU ŞEKİLDE BAĞLANILMAYACAK
        self.stub = rc_grpc.mainRouterServerStub(self.channel)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def detectCourtLines(self, data):
        requestData = rc.requestData(data=self.obj2bytes(data))
        response = self.stub.detectCourtLinesController(requestData)
        return response.data

    def startGameObservation(self, data):
        requestData = rc.requestData(data=self.obj2bytes(data))
        response = self.stub.gameObservationController(requestData)
        return response.data, response.frame

    def getProducerThreads(self):
        requestData = rc.requestData(data=self.obj2bytes(b""))
        response = self.stub.getProducerThreads(requestData)
        th=self.bytes2obj(response.data)
        return th

    def stopProduce(self, data):
        requestData = rc.requestData(data=self.obj2bytes(data))
        responseData = self.stub.stopProduce(requestData)
        return responseData.data

    def getRunningConsumers(self):
        requestData = rc.requestData(data=b"")
        msg = self.stub.getRunningConsumers(requestData)
        return self.bytes2obj(msg.data)

    def stopRunningConsumer(self, data):
        requestData = rc.requestData(data=self.obj2bytes(data))
        responseData = self.stub.stopRunningConsumer(requestData)
        return responseData.data

    def stopAllRunningConsumers(self):
        requestData = rc.requestData(data=b"")
        msg = self.stub.stopAllRunningConsumers(requestData)
        return msg.data

    def disconnect(self):
        self.channel.close()


if __name__ == "__main__":
    import cv2
    import argparse
    import numpy as np

    def bytes2img(image):
        nparr = np.frombuffer(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=int, required=True)
    args = parser.parse_args()

    mc = MainClient()
    
    # DATAS BY SENT CLIENT
    data={}
    data["id"] = 9
    data["force"] = False
    data["limit"] = -1

    data["aos_type_id"] = 6 # 3-5-6
    data["player_id"] = 1
    data["court_id"] = 1
    
    data["stream_id"] = 1
    data["ball_position_area"] = []
    data["ball_fall_array"] = []
    data["player_position_area"] = []

    # INNER
    data["consumer_thread_name"] = ""
    data["producer_thread_name"] = ""

    TEST=args.test

    if TEST==1:
        res = mc.detectCourtLines(data)
        points = mc.bytes2obj(res)
        logger.info(points)

        # PRINT
        cam = cv2.VideoCapture(f"/srv/nfs/mydata/docker-tennis/assets/video_{data['id']}.mp4")
        ret, cimage = cam.read()

        #line_data, point_area_data, cimage = extractSpecialLocations(points, cimage, AOS_TYPE=3)

        for i, line in enumerate(points):
            if len(line)>0:
                cimage = cv2.line(cimage, ( int(line[0]), int(line[1]) ), ( int(line[2]), int(line[3]) ), (66, 245, 102), 3)
            if i==10:
                break

        cv2.imshow("", cimage)
        cv2.waitKey(0)
        cam.release()


    elif TEST==2:
        res, canvas = mc.startGameObservation(data)
        resdata = mc.bytes2obj(res) # "score", "fall_point"
        canvas = bytes2img(canvas)

        score = resdata["score"]
        points = resdata["fall_point"]
        logger.info(f"PUAN: {score} ")

        # PRINT
        if points is not None:
            for p in points:
                cimage = cv2.circle(canvas, (int(p[0]),int(p[1])), 5, (0,255,0),1)
                cimage = cv2.putText(cimage, f"Score: {score}",(960, 720), cv2.FONT_HERSHEY_TRIPLEX, 1, (255,255,255))
            cv2.imshow("", cimage)
            cv2.waitKey(0)
        else:
            print("Düşme Noktası Bulunamadı.!")

    elif TEST==3:
        producers = mc.getProducerThreads()
        consumers = mc.getRunningConsumers()
        logger.info(f"PRODUCERS: {producers}")
        logger.info(F"CONSUMERS: {consumers}")


    elif TEST==4:
        consumers = mc.getRunningConsumers()
        res = mc.stopRunningConsumer(data)
        consumers = mc.getRunningConsumers()


    elif TEST==5:
        res = mc.stopProduce(data)