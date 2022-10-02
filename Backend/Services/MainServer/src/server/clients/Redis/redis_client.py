from __future__ import print_function
import pickle
import grpc
import clients.Redis.redisCache_pb2 as rc
import clients.Redis.redisCache_pb2_grpc as rc_grpc

class RedisCacheManager():

    def __init__(self):
        self.channel = grpc.insecure_channel('redisservice:50051') #redisservice:50051
        self.stub = rc_grpc.redisCacheStub(self.channel)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def Read(self, query, force=False):
        requestData = rc.ReadRequest(query=query, force=force)
        response = self.stub.Read(requestData)
        return response.data
    
    def Write(self, query, value):
        queryData = {}
        queryData["query"] = query
        queryData["value"] = value

        # Bytes tipinde değilse çevir.
        if not isinstance(queryData, bytes):
            queryData= self.obj2bytes(queryData)

        requestData = rc.WriteRequest(query=queryData)
        response = self.stub.Write(requestData)
        return response.key

    def disconnect(self):
        self.channel.close()


if __name__ == "__main__":
    rcm = RedisCacheManager()
    QUERY = f'''SELECT name, source, court_line_array, kafka_topic_name FROM public."Stream" WHERE id=28 AND is_activated=true'''
    streamData = rcm.Read(query=QUERY, force=False)
    val = pickle.loads(streamData)
    print(val)