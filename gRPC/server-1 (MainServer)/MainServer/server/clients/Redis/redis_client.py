from __future__ import print_function
import logging
import pickle
import grpc
import clients.Redis.redisCache_pb2 as rc
import clients.Redis.redisCache_pb2_grpc as rc_grpc

class RedisCacheManager():

    def __init__(self):
        self.channel = grpc.insecure_channel('redisservice:50051')
        self.stub = rc_grpc.redisCacheStub(self.channel)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def isCached(self, query):
        requestData = rc.isCachedDataRequest(query=query)
        response = self.stub.isCached(requestData)
        return response.data
    
    def writeCache(self, query, value):
        queryData = {}
        queryData["query"] = query
        queryData["value"] = value

        # Bytes tipinde değilse çevir.
        if not isinstance(queryData, bytes):
            queryData= self.obj2bytes(queryData)

        requestData = rc.writeCacheRequest(query=queryData)
        response = self.stub.writeCache(requestData)
        return rc.writeCacheResponse(key=response.key)

    """
    def readCache(self, key):
        pass
    """
    
    def disconnect(self):
        self.channel.close()