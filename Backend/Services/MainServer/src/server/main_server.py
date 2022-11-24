import collections
import logging
import multiprocessing
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
from WorkManager import WorkManager

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)


def MainProcess():
    processManager = ProcessManager()
    processManager.process()


MAX_WORKERS:int = 10
MAX_CONCURENT_WORKERS:int = 1
#*SERVER
class MainServer(rc_grpc.MainServerServicer):
    
    def __init__(self):
        super().__init__()
        self.rcm = RedisCacheManager()
        self.workManager = WorkManager()
        self.consumer = KafkaConsumerManager()
        self.currentThreads = collections.defaultdict(list)


    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)


    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)


    def getStreamProcess(self, id):
        return Repositories.getProcessRelatedById(self.rcm, id)


    def DeployNewProcess(self, data):
        t = threading.Thread(name=data["topicName"], target=self.workManager.ProcessData, args=[data,])
        t.start()
        return t


    def StartProcess(self, request, context):
        logging.info(f"Process:{request.ProcessId} işlenmeye başladı")
        raw = self.getStreamProcess(request.ProcessId)
        
        if len(raw) < 1:
            raise "Bu process ile ilgili bilgi bulunamadı."
        data = raw[0]

        if len(self.currentThreads) >= MAX_CONCURENT_WORKERS:
            Repositories.markAsCompleted(self.rcm, request.ProcessId)
            raise "Maksimum işlem sayısını geçtiniz. Önceki işlemlerin bitmesini bekleyiniz."

        data, send_queue, empty_message, RESPONSE_ITERATOR = self.workManager.Prepare(data)

        # Yeni bir thread de işlem başlat
        t = self.DeployNewProcess(data)
        
        # Process Adı -> [Topic Adı, Bool] şeklinde çalışan threadlerin listesini tut.
        self.currentThreads[request.ProcessId] = [data["topicName"], True]

        frameCounter = 0
        try:
            for response in RESPONSE_ITERATOR:
                flag = self.currentThreads.get(request.ProcessId, None)
                if flag is not None:
                    if not flag[1]:
                        send_queue.put(None)

                if not context.is_active():
                    send_queue.put(None)

                frame_base64 = ""
                if response.Response.Data != b"":
                    bframe = Converters.Bytes2Frame(response.Response.Data)
                    frame_base64 = Converters.Frame2Base64(bframe)
                frameCounter+=1
                yield rc.StartProcessResponseData(Message=f"{request.ProcessId} numaralı process işleme alındı.", Data="[]", Frame=frame_base64)

                send_queue.put(empty_message)
        except:
            logging.info(f"Iteratordan çıktı. Returned Frame Count: {frameCounter}")

        logging.info("Ana işlemin bitmesi bekleniyor...")
        t.join()

        Repositories.markAsCompleted(self.rcm, data["process_id"])
        currentRemovedProcess = self.currentThreads.get(request.ProcessId, None)
        if currentRemovedProcess is not None:
            x = self.currentThreads.pop(request.ProcessId)

        logging.info(f"BİTTİ: {data['process_id']}")
    

    def StopProcess(self, request, context):
        process = self.currentThreads.get(request.ProcessId, None)
        if process is not None:
            try:
                self.currentThreads[request.ProcessId][1] = False
                response = self.workManager.stopProducer(process[0])
                return rc.StopProcessResponseData(Message=response, flag = True)
            except Exception as e:
                logging.info(e)

        return rc.StopProcessResponseData(Message="İşlem Bulunamadı.", flag = False)


def serve():
    mainServer = MainServer()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))
    rc_grpc.add_MainServerServicer_to_server(mainServer, server)
    server.add_insecure_port('[::]:50011')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.info("MAIN SERVER BAŞLADI!")

    MainP1 = multiprocessing.Process(target=MainProcess, daemon=True)
    MainP2 = multiprocessing.Process(target=serve, daemon=False)
    MainP1.start()
    MainP2.start()
    MainP2.join()
    
    logging.warning("MAIN SERVER ÇALIŞMAYI DURDURDU!")