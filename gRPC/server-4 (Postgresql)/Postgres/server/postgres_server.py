import logging
from concurrent import futures
import json
import pickle
import grpc
import postgresql_pb2 as rc
import postgresql_pb2_grpc as rc_grpc
from libs.postgresManager import PostgresManager

class postgresServer(rc_grpc.postgresqlServicer):
    def __init__(self):
        super().__init__()
        self.postgresManager = PostgresManager()

    def obj2bytes(self, obj):
        return pickle.dumps(obj)

    def bytes2obj(self, bytes):
        return pickle.loads(bytes)

    def connect2DB(self, request, context):
        res = self.postgresManager.connect2(host=request.host, database=request.database, user=request.user, password=request.password)
        responseData = rc.connect2DBResponse(result=res)
        return responseData

    def disconnectDB(self, request, context):
        responseData = self.postgresManager.disconnect()
        return rc.disconnectDBResponse(result=responseData)

    def executeSelectQuery(self, request, context):
        response=None
        res=[]
        try:
            query_obj=self.bytes2obj(request.query)
            response = self.postgresManager.executeSelectQuery(query_obj["query"])
            response = self.bytes2obj(response)
        except Exception as e:
            logging.info("ERROR(executeSelectQuery): ", e)

        #TODO Dinamik olarak memoryviewler düzenlenecek: 2
        if response is not None:
            for item in response[0]:
                type(item)
                if isinstance(item, memoryview):
                    res.append(bytes(item))
                else:
                    res.append(item)

        responseData = rc.executeSelectQueryResponse(result=self.obj2bytes(res))
        return responseData

    def executeInsertQuery(self, request, context):
        query_obj=self.bytes2obj(request.query)
        res = self.postgresManager.executeCommitQuery(query_obj["query"], query_obj["values"])
        responseData = rc.executeInsertQueryResponse(result="ok")
        return responseData

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_postgresqlServicer_to_server(postgresServer(), server)
    server.add_insecure_port('[::]:50041')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()