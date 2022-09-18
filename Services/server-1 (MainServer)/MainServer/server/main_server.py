import collections
from concurrent.futures import thread
import multiprocessing
import pickle
from concurrent import futures

import grpc

import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from clients.Redis.redis_client import RedisCacheManager
from libs.helpers import Converters, Repositories
from ProcessManager import ProcessManager
from StatusChecker import StatusChecker
from WorkManager import WorkManager

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
        self.currentProcesses = collections.defaultdict(list)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def getStreamProcess(self, id):
        return Repositories.getProcessRelatedById(self.rcm, id)

    def StartProcess(self, request, context):
        print("Başladı")
        data = self.getStreamProcess(request.ProcessId)
        if len(data) > 0:

            if len(data[0])>0:
                modified_data = self.workManager.Prepare(data[0])
                # p = multiprocessing.Process(name=modified_data["topicName"], target=self.workManager.ProducerController, args=[modified_data,])
                # p.start()
                # self.currentProcesses[request.ProcessId] = p

                topicName = modified_data["topicName"]
                if isinstance(topicName, str):
                    gen = self.consumer.consumer(topicName, f"Process_{request.ProcessId}_UI", -1, "earliest")
                    for frame_byte in gen:
                        if not context.is_active():
                            break
                        frame_base64 = Converters.frame2base64(Converters.bytes2frame(frame_byte.data))
                        yield rc.StartProcessResponseData(Message=f"{request.ProcessId} numaralı process işleme alındı.", Data="[]", Frame=frame_base64)

            # p.join()
        print("BİTTİ")
    
    def StopProcess(self, request, context):
        ProcessName = self.workManager.currentProcess.get(request.ProcessId, None)
        if ProcessName is not None:
            response = self.workManager.stopProducer(ProcessName)
            return rc.StopProcessResponseData(Message=response, flag = True)
        
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
