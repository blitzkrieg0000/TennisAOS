import multiprocessing
import pickle
import time
from concurrent import futures
from email import message

import grpc

import MainServer_pb2 as rc
import MainServer_pb2_grpc as rc_grpc
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
        self.processes = multiprocessing.Manager().dict() #SHARED MEMORY OBJECT0
        self.algorithmManager = WorkManager()
        # self.mainProcess = multiprocessing.Process(name="MAIN_SERVER_PROCESS", target=self.MainProcess)
        # self.mainProcess.start()
        
    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def getStreamProcess(self, id):
        query_keys = ["process_id", "process_name", "session_id", "stream_id", "aos_type_id", "player_id", "court_id", "limit", "force","stream_name", "source", "court_line_array", "kafka_topic_name", "is_video"]
        QUERY = f'SELECT p.id as process_id, p.name as process_name, sp.id as session_id, st.id, sp.aos_type_id, sp.player_id, sp.court_id,sp."limit", sp."force", st."name", st."source", st.court_line_array, st.kafka_topic_name, st.is_video\
        FROM public."Process" as p\
        INNER JOIN public."SessionParameter" as sp\
        ON sp.id = p.session_id\
        INNER JOIN public."ProcessParameters" as pp\
        ON pp.id = p.id\
        INNER JOIN public."Stream" as st\
        ON (CASE WHEN pp.stream_id IS NULL THEN st.id = sp.stream_id ELSE st.id = pp.stream_id END)\
        WHERE p.is_completed=true AND p.id={id}'
        processData = self.rcm.Read(query=QUERY, force=True)
        processes = Converters.bytes2obj(processData)
        if processes is not None:
            return [dict(zip(query_keys, process)) for process in processes]
        return []

    def StopProcess(self, request, context):
        ProcessName = self.algorithmManager.currentProcess.get(request.ProcessId, None)
        if ProcessName is not None:
            response = self.algorithmManager.stopProducer(ProcessName)
            return rc.StopProcessResponseData(message=response, flag = True)
        return rc.StopProcessResponseData(message="İşlem Bulunamadı.", flag = False)

    def StartProcess(self, request, context):
        data = self.getStreamProcess(request.ProcessId)
        if len(data) > 0:
            #self.processes[request.ProcessId] = data['kafka_topic_name']
            results = self.algorithmManager.StartGameObservationController(data[0])
            Repositories.markAsCompleted(self.rcm, data["process_id"])

            return rc.StartProcessResponseData(Message=f"{request.ProcessId} numaralı process işleme alındı.", Data="[]")
        return rc.StartProcessResponseData(Message=f"{request.ProcessId} için process bulunmadı.", Data="[]")

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
