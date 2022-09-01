from libs.logger import logger
from concurrent import futures
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

        try:
            query_obj=self.bytes2obj(request.query)
            response = self.postgresManager.executeSelectQuery(query_obj["query"])
        except Exception as e:
            logger.warning("ERROR(executeSelectQuery): ", e)

        

        responseData = rc.executeSelectQueryResponse(result=self.obj2bytes(response))
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
    serve()