import hashlib
import logging
import pickle
from concurrent import futures

import grpc

import redisCache_pb2 as rc
import redisCache_pb2_grpc as rc_grpc
from clients.Postgres.postgres_client import PostgresDatabaseClient
from libs.redisManager import RedisManager

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

#*SERVER
class redisCache(rc_grpc.redisCacheServicer):
    def __init__(self):
        super().__init__()
        self.rm = RedisManager()
        self.pDC = PostgresDatabaseClient()

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def Sha256(self, str) -> str:
        return hashlib.sha256(str.encode('utf-8')).hexdigest()
    
    def Read(self, request, context):
        value = None
        key:str = self.Sha256(request.query)
        
        if request.force:
            self.rm.delete(key)

        if self.rm.isExist(key) and self.rm.setExpire(key, 60):
            value = self.rm.read(key)
        else:
            conn_info = self.pDC.connect2DB()
            value = self.pDC.executeSelectQuery(request.query)
            self.rm.write(key, value)

        self.rm.setExpire(key, 60)

        return rc.ReadResponse(data=value)

    def Write(self, request, context):
        query = self.bytes2obj(request.query)
        self.pDC.connect2DB()
        resultMessage = self.pDC.executeInsertQuery(query["query"], query["value"])
        return rc.WriteResponse(key=resultMessage)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_redisCacheServicer_to_server(redisCache(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
