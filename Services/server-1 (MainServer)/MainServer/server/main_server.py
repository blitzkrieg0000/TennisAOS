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
MAX_WORKERS = 5

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
        self.processes = multiprocessing.Manager().dict() #SHARED MEMORY OBJECT0
        self.workManager = WorkManager()
        self.executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.consumer = KafkaConsumerManager()
        # self.mainProcess = multiprocessing.Process(name="MAIN_SERVER_PROCESS", target=self.MainProcess)
        # self.mainProcess.start()
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def getStreamProcess(self, id):
        return Repositories.getProcessRelatedById(self.rcm, id)

    def GetStreamingFrame(self, request, context):
        print(request.ProcessId)
        print(self.workManager.currentProcess)
        threadName = self.workManager.currentProcess[request.ProcessId] 
        print(threadName)
        if isinstance(threadName, str):
            gen = self.consumer.consumer(threadName, "UI", -1)
            for frame_byte in gen:
                frame_base64 = Converters.frame2base64(Converters.bytes2frame(frame_byte.data))
                #TODO Frame Arayüz tarafından tutularak son kullanıcıya gösterilecek.
                yield rc.GetStreamingFrameResponseData(Frame=frame_base64)
        return rc.GetStreamingFrameResponseData(Frame=b"Frame Yok")

    def StartProcess(self, request, context):
        data = self.getStreamProcess(request.ProcessId)
        if len(data) > 0:
            
            def callback(future):
                Repositories.markAsCompleted(self.rcm, data[0]["process_id"])
            
            threadSubmit = self.executor.submit(self.workManager.StartGameObservationController,data[0])
            futureIterator = futures.as_completed(threadSubmit)
            
            threadSubmit.add_done_callback(callback)
            return rc.StartProcessResponseData(Message=f"{request.ProcessId} numaralı process işleme alındı.", Data="[]", Frame="")
        
        return rc.StartProcessResponseData(Message=f"{request.ProcessId} için process bulunmadı.", Data="[]")
    
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
