from asyncio.log import logger
import hashlib
from concurrent import futures

import grpc

import redisCache_pb2 as rc
import redisCache_pb2_grpc as rc_grpc
from clients.Postgres.postgres_client import PostgresDatabaseClient
from libs.redisManager import RedisManager

#*SERVER
class redisCache(rc_grpc.redisCacheServicer):
    def __init__(self):
        super().__init__()
        self.rm = RedisManager()
        self.pDC = PostgresDatabaseClient()

    def Sha256(self, str) -> str:
        return hashlib.sha256(str.encode('utf-8')).hexdigest()
    
    def Read(self, request, context):
        query:str = request.query
        key:str = self.Sha256(query)
        
        if self.rm.isExist(key):
            keyType = self.rm.getType(key)
            # TODO Tipine göre okuma yap şuan sadece byte okuyor. Byte ve Json verileri "string" olarak geçiyor
            value = self.rm.read(key, val_type=None)
            logger.info(value)
        else:
            conn_info = self.pDC.connect2DB()
            value = self.pDC.executeSelectQuery(query)

            if not isinstance(value, bytes):
                value = self.obj2bytes(value)

            self.rm.write(key, value)

        if request.force:
            self.rm.delete(key)
        else:
            self.rm.setExpire(key, 60)

        responseData = rc.isCachedResponse(data=value)
        return responseData

    def Write(self, request, context):
        query = self.bytes2obj(request.query)
        #TODO Redis + Postgrese kaydet
        self.pDC.connect2DB()
        resultMessage = self.pDC.executeInsertQuery(query["query"], query["value"])
        responseData = rc.writeCacheResponse(key=resultMessage)
        return responseData

    """
    def readCache(self, request, context):
        #TODO REDIS CACHE CONTROL -> data
        responseData = rc.Result(data="SCORE 10")
        return responseData
    """

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_redisCacheServicer_to_server(redisCache(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()