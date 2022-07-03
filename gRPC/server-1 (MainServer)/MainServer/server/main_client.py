from __future__ import print_function
import logging
import pickle
import grpc
import mainRouterServer_pb2 as rc
import mainRouterServer_pb2_grpc as rc_grpc
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)
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
        return self.bytes2obj(response.data)

    def getProducerThreads(self):
        requestData = rc.requestData(data=self.obj2bytes(b""))
        response = self.stub.getProducerThreads(requestData)
        th=self.bytes2obj(response.data)
        logging.info(f"PRODUCER THREADS: {th}")
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
    import numpy as np

    mc = MainClient()

    ayarlar={"id":1, "force": False}

    # DATAS BY SENT CLIENT
    data={}
    data["id"] = 1               
    data["force"] = False
    data["limit"] = -1

    data["player_id"] = 1
    data["court_id"] = 1
    data["aos_type_id"] = 3
    data["stream_id"] = 1
    data["score"] = 4
    data["ball_position_area"] = []
    data["player_position_area"] = []
    

    TEST=2


    if TEST==1:
        res = mc.detectCourtLines(data)

        logging.info(res)
        points = mc.bytes2obj(res)

        cam = cv2.VideoCapture("/home/blitzkrieg/source/repos/TennisAOS/gRPC/assets/videos/throw_videos/throw_2.mp4")
        ret, cimage = cam.read()
        for i, line in enumerate(points):
            if len(line)>0:
                cimage = cv2.line(cimage, ( int(line[0]), int(line[1]) ), ( int(line[2]), int(line[3]) ), (66, 245, 102), 3)
            if i==10:
                break

        cv2.imshow("", cimage)
        cv2.waitKey(0)
        cam.release()

    elif TEST==2:
        res = mc.startGameObservation(data)
        cam = cv2.VideoCapture("/home/blitzkrieg/source/repos/TennisAOS/gRPC/assets/videos/throw_videos/throw_2.mp4")
        ret, cimage = cam.read()
        for p in res:
            cimage = cv2.circle(cimage, (int(p[0]),int(p[1])), 5, (0,255,0),1)

        cv2.imshow("", cimage)
        cv2.waitKey(0)

    elif TEST==3:
        #!GET STREAMING THREADS
        res = mc.getProducerThreads()

        data = mc.getRunningConsumers()
        logging.info(data)

    elif TEST==4:
        data = {}
        data["consumer_thread_name"] = "tenis_saha_1-0-55826760874526647746697030151880964752"
        res = mc.stopRunningConsumer(data)

    elif TEST==5:
        data= {}
        data["producer_thread_name"] = ""
        res = mc.stopProduce(data)