from concurrent import futures
import multiprocessing
import threading
import time

import grpc
import testServer_pb2 as rc
import testServer_pb2_grpc as rc_grpc

class MainServer(rc_grpc.TestServerServicer):
    EXCEPT_PREFIX = ['']
    def __init__(self):
        super().__init__()
        self.counter = 0

    def info(self):
        for x in range(100):
            time.sleep(1)
            print(x)

    def Process(self, request, context):
        print(f"Başladı : {threading.get_ident()}")
        context.add_callback(lambda : print(f"Uyarı, RPC sonlandırıldı : {threading.get_ident()}: {self.counter}"))
        
        p = multiprocessing.Process(target=self.info)
        p.start()

        print(f"Parent Process: {multiprocessing.current_process()}")
        print(f"ChildProcesses: {multiprocessing.active_children()}")

        time.sleep(3)

        while p.is_alive():
            if not context.is_active():
                if p.is_alive():
                    p.terminate()
                    p.join(time=1)
                    if p.is_alive:
                        p.kill()
                p.close()
                del p
                # context.Cancel()
                context.set_code(grpc.StatusCode.CANCELLED)
                context.set_details('RPC Client Tarafından Sonlandırıldı.')
                return rc.responseData()
                
        return rc.responseData(data=f"Sonuçlandı.")
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    rc_grpc.add_TestServerServicer_to_server(MainServer(), server)
    server.add_insecure_port('[::]:9999')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
