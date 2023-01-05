import collections
import logging
import multiprocessing
import threading
from concurrent import futures
from types import SimpleNamespace

import grpc
import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc
from clients.Redis.redis_client import RedisCacheManager
from clients.StreamKafka.Consumer.consumer_client import KafkaConsumerManager
from libs.DefaultChain.PrepareProcessChain import PrepareProcessChain
from libs.helpers import Converters, Repositories, Tools
from libs.WorkManager import WorkManager
from ProcessManager import ProcessManager

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
        self.prepareProcessChain = PrepareProcessChain()
        self.currentThreads = collections.defaultdict(list)
    

    def AddWork(self, id, topicName):
        currentWork = SimpleNamespace()
        currentWork.name = topicName
        currentWork.status = True
        self.currentThreads[id] = currentWork


    def RemoveWork(self, id):
        if self.currentThreads.get(id, None):
            currentWork = self.currentThreads.pop(id)
            logging.info(f"Sonlandırılan ProcessId: {id}")

            return currentWork


    def GetWork(self, id):

        return self.currentThreads.get(id, None)


    def CheckWork(self, id):
        flag = self.currentThreads.get(id, None)
        if flag is not None:
            return flag.status

        return None   


    def QueryDatabaseForRequestedProcess(self, process_id):
        #! Database sorgusu gerçekleştir.
        raw = Repositories.getProcessRelatedById(self.rcm, process_id)
        if len(raw) < 1:
            msg = f"Process ID: {process_id} ile ilgili bilgi bulunamadı."
            logging.warning(msg)
            raise msg
        data = raw[0]
        logging.info(f"Process: {int(process_id)} işlenmeye başladı.")
        return data


    def DeployWork(self, data):
        t = threading.Thread(name=data["data"]["topicName"], target=self.workManager.ProcessStreamData, kwargs=data)
        t.start()
        
        return t


    def CheckLimitForStartProcess(func):
        def wrapper(self, request, context):

            if len(self.currentThreads) >= MAX_CONCURENT_WORKERS:
                Repositories.markAsCompleted(self.rcm, request.ProcessId)
                msg = "Maksimum işlem sayısını geçtiniz. Sıradaki işlemlerin bitmesini bekleyiniz."
                logging.warning(msg)
                raise msg

            return func(self, request, context)

        return wrapper


    @CheckLimitForStartProcess
    def StartProcess(self, request, context):

        data = self.QueryDatabaseForRequestedProcess(request.ProcessId)

        # Producer'ı stream_name den oluşan bir Topic ile ayağa kaldır.
        arr = {
            "data" : data,
            "independent" : False,
            "errorLimit" : 3
        }
        results = self.prepareProcessChain.Handle(**arr)
        send_queue = results["send_queue"]
        empty_message = results["empty_message"]
        RESPONSE_ITERATOR = results["responseIterator"]
        data = results["data"]

        # Bu process id yi yapılan işlere ekle
        self.AddWork(request.ProcessId, data["topicName"])

        # Yeni bir thread de video işlemeyi başlat
        t = self.DeployWork(results)
        
        frameCounter = 0
        try:
            for response in RESPONSE_ITERATOR:
                
                # Durdurma kriterleri
                if not self.CheckWork(request.ProcessId) or not context.is_active():
                    send_queue.put(None)

                # UI ya giden görüntü neyse, işleme alınan görüntü de o olacak. 
                # Bunun için bidirectional grpc metodu tanımlandı. 
                # Buradaki sentinel iteratorı besledikçe bize 1 adet frame gidiyor.
                # Kısaca 1-request için 1 adet video karesi geliyor.
                frame_base64 = ""
                if response.Response.Data != b"":
                    bframe = Converters.Bytes2Frame(response.Response.Data)
                    frame_base64 = Converters.Frame2Base64(bframe)
                frameCounter+=1
                msg = f"{request.ProcessId} numaralı process işleme alındı."

                yield rc.StartProcessResponseData(Message=msg, Data="[]", Frame=frame_base64)

                send_queue.put(empty_message) # Yeni 1 adet frame almak için request yap
        except:
            logging.info(f"Iteratordan çıktı. Returned Frame Count: {frameCounter}")

        logging.info("Ana işlemin bitmesi bekleniyor...")
        t.join() # Videonun işlenmesini bekle

        Repositories.markAsCompleted(self.rcm, data["process_id"])
        _ = self.RemoveWork(request.ProcessId)
    

    def StopProcess(self, request, context):
        if self.CheckWork(request.ProcessId):
            currentWork = self.RemoveWork(request.ProcessId)
            if currentWork:
                response = self.workManager.stopProducer(currentWork.name)
                return rc.StopProcessResponseData(Message=response, flag=True)

        return rc.StopProcessResponseData(Message=f"İşlem Bulunamadı: ProcessID: {request.ProcessId} ", flag=False)


    def MergeData(self, request, context):
        #Eğer Topic Varsa
        ProcessId = request.ProcessId
        topicName = ""
        FrameIterator = self.consumer.consumer(topicName, f"MergeData_{Tools.getUID()}")

        for item in FrameIterator:
            frame = Converters.Bytes2Frame(item.data)
            if frame is not None:
                ...

        #Eğer Topic Yoksa: Videodan çek


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