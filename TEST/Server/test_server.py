from concurrent import futures
import logging
import multiprocessing
import threading
import time

import grpc
import testServer_pb2 as rc
import testServer_pb2_grpc as rc_grpc
logging.basicConfig(level=logging.NOTSET)

class cGen():
    def __init__(self) -> None:
        self.counter = 0
        self.stopFlag = False

    def stopGen(self):
        self.stopFlag = True

    def __iter__(self):
        return self

    def __next__(self):
        if self.counter==10 or self.stopFlag==True:
            raise StopIteration
        self.counter = 1+self.counter
        return self.counter

class MainServer(rc_grpc.TestServerServicer):
    EXCEPT_PREFIX = ['']
    def __init__(self):
        super().__init__()
        self.counter = 0

    def Process(self, request, context):
        print(type(request),type(context))
        
        for x in cGen():

            if not context.is_active():
                logging.warning("RPC Client Sonlandırıldığı için server-side sonlandırılıyor...")
                context.set_code(grpc.StatusCode.CANCELLED)
                context.set_details('RPC Client Sonlandırıldığı için server-side sonlandırıldı.')
                return rc.responseData()
                
            logging.info(f"{x}")
            yield rc.responseData(data=f"{x}")
            time.sleep(1)

        logging.info("Çıkış yapılıyor")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    rc_grpc.add_TestServerServicer_to_server(MainServer(), server)
    server.add_insecure_port('[::]:9999')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
