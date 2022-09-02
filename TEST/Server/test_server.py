from concurrent import futures
import threading
import time
import grpc
import testServer_pb2 as rc
import testServer_pb2_grpc as rc_grpc

class MainServer(rc_grpc.TestServerServicer):
    EXCEPT_PREFIX = ['']
    def __init__(self):
        super().__init__()

    def Process(self, request, context):
        thread = threading.currentThread().ident
        context.add_callback(lambda : print(f"Uyarı, RPC sonlandırıldı : {thread}"))

        for x in range(10):
            time.sleep(2)
            if not context.is_active():
                # context.Cancel()
                context.set_code(grpc.StatusCode.CANCELLED)
                context.set_details('RPC Client Tarafından Sonlandırıldı.')
                return rc.responseData()

            print(thread)
            yield rc.responseData(data=f"Server Çalışıyor. {x} {threading.currentThread().ident}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rc_grpc.add_TestServerServicer_to_server(MainServer(), server)
    server.add_insecure_port('[::]:9999')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
