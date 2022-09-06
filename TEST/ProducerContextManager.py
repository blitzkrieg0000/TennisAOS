import logging
import multiprocessing
import signal
import sys
import time

logging.basicConfig(level=logging.NOTSET)

class ProducerContextManager():
    def __init__(self):
        self._sigint = None
        self._sigterm = None

    def _handler(self, signum, frame):
        logging.warning("Received SIGINT or SIGTERM! Finishing producer, then exiting.")
        sys.exit(0)

    def __enter__(self):
        self._sigint = signal.signal(signal.SIGINT, self._handler)
        self._sigterm = signal.signal(signal.SIGTERM, self._handler)
        return self
     
    def __exit__(self, exc_type, exc_value, exc_traceback):
        print('exit method called')
        signal.signal(signal.SIGINT, self._sigint)
        signal.signal(signal.SIGTERM, self._sigterm)

    def producer(self):
        logging.info(f"Producer Deploying")
        
        for x in range(100):

            if x == 30:
                break

            time.sleep(1)
            print(x)


def streamProducer():
    with ProducerContextManager() as manager:
        print('with statement block')
        manager.producer()


p = multiprocessing.Process(target=streamProducer)
p.start()  

time.sleep(5)
p.terminate()
time.sleep(5)
active_process = multiprocessing.active_children()
print(active_process)
print(p.is_alive())
print("exit")