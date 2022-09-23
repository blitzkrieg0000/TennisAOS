import collections
import logging
import pickle
import threading
from concurrent import futures

import grpc

import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from libs.helpers import Converters, Repositories
from ProcessManager import ProcessManager
from StatusChecker import StatusChecker
from WorkManager import WorkManager

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.NOTSET)

def logo():
    f = open("Services/server-1 (MainServer)/MainServer/server/libs/logo.txt", "r")
    logo = f.read()
    f.close()
    print(logo, "\n")

#*SERVER
class MainServer(rc_grpc.MainServerServicer):
    
    def __init__(self):
        super().__init__()
        self.rcm = RedisCacheManager()
        self.workManager = WorkManager()
        self.consumer = KafkaConsumerManager()
        self.currentThreads = collections.defaultdict(list)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def getStreamProcess(self, id):
        return Repositories.getProcessRelatedById(self.rcm, id)

    def StartProcess(self, request, context):
        logging.info(f"Process:{request.ProcessId}  Başladı")
        raw = self.getStreamProcess(request.ProcessId)
        if len(raw) > 0:
            data = raw[0]
            data, send_queue, emptyRequest, responseIterator = self.workManager.Prepare(data)

            t = threading.Thread(name=data["topicName"], target=self.workManager.ProducerController, args=[data,])
            t.start()
            
            topicName = data["topicName"]
            self.currentThreads[request.ProcessId] = [topicName, True]

            try:
                for response in responseIterator:
                    
                    flag = self.currentThreads.get(request.ProcessId, None)
                    if not flag:
                        if not flag[1]:
                            break
    
                    if not context.is_active():
                        break
                    frame_base64 = Converters.frame2base64(Converters.bytes2frame(response.frame))
                    yield rc.StartProcessResponseData(Message=f"{request.ProcessId} numaralı process işleme alındı.", Data="[]", Frame=frame_base64)
                    send_queue.put(emptyRequest)
                    
                    print(frame_base64[:10])
            except:
                print("iterator dan çıktı.")

            print("Ana işlemin bitmesi bekleniyor...")
            t.join()
            Repositories.markAsCompleted(self.rcm, data["process_id"])
            
        print(f"BİTTİ")
    
    def StopProcess(self, request, context):
        process = self.currentThreads.get(request.ProcessId, None)
        if process is not None:
            try:
                self.currentThreads[request.ProcessId][1] = False
                response = self.workManager.stopProducer(process[0])
                return rc.StopProcessResponseData(Message=response, flag = True)
            except Exception as e:
                print(e)

        return rc.StopProcessResponseData(Message="İşlem Bulunamadı.", flag = False)

    def MainProcess(self):
        while True:
            statusChecker = StatusChecker()
            processManager = ProcessManager()

            statusChecker.set_next(processManager)
            processManager.set_next(statusChecker)

            data = statusChecker.handle([])
            del statusChecker
            del processManager


def serve():
    logo()
    mainSrv = MainServer()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_MainServerServicer_to_server(mainSrv, server)
    server.add_insecure_port('[::]:50011')
    server.start()
    server.wait_for_termination()
    # mainSrv.mainProcess.join()


if __name__ == '__main__':
    serve()
