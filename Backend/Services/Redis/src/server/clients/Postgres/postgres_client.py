from __future__ import print_function
import grpc
import clients.Postgres.postgresql_pb2 as rc
import clients.Postgres.postgresql_pb2_grpc as rc_grpc
import pickle

class PostgresDatabaseClient():
    def __init__(self) -> None:
        self.channel = grpc.insecure_channel('postgresservice:50041')
        self.stub = rc_grpc.postgresqlStub(self.channel)

    def connect2DB(self, host="postgres", database="tenis", user="tenis", password="2sfcNavA89A294V4"):
        requestData = rc.connect2DBRequest(host=host, database=database, user=user, password=password)
        response = self.stub.connect2DB(requestData)
        return response.result

    def disconnectDB(self):
        self.stub.disconnectDB()

    def Bytes2Obj(self, bytes):
        return pickle.loads(bytes)

    def Obj2Bytes(self, obj):
        return pickle.dumps(obj)

    def executeSelectQuery(self, query):
        query_obj={"query": query}
        requestData = rc.executeSelectQueryRequest(query=self.Obj2Bytes(query_obj))
        response = self.stub.executeSelectQuery(requestData)
        return response.result

    def executeInsertQuery(self, query, values):
        query_obj={}
        query_obj["query"] = query
        query_obj["values"] = values
        requestData= rc.executeInsertQueryRequest(query=self.Obj2Bytes(query_obj))
        response = self.stub.executeInsertQuery(requestData)
        return response.result

    def disconnect(self):
        self.channel.close()