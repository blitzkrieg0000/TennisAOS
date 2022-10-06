import threading
import time
import concurrent.futures

threadLock = threading.Lock()

class Process():
    
    counter = 0

    def __init__(self):
        pass

    
    def sonsuz(self):
        while True:
            pass


    def bekle(self, x):
        print([item.name for item in threading.enumerate()])
        tn = threading.current_thread().name
        print("Başladı:",tn)
        time.sleep(x)
        print("Bitti:",tn)

        f = open("TEST/dump.txt", "a")
        f.write(f"Bitti:{tn}\n")
        f.close()


    def arttir(self):
        tn = threading.current_thread().name
        print("Başladı:",tn)
        threadLock.acquire()
        threadLock.release()
        time.sleep(5)
        self.counter = 1 + self.counter
        print("Bitti:",tn)

    def azalt(self):
        tn = threading.current_thread().name
        print("Başladı:",tn)
        threadLock.acquire()
        threadLock.release()
        time.sleep(5)
        self.counter = -1 + self.counter

        print("Bitti:",tn)

processManager = Process()

# thread_1 = threading.Thread(name="Thread-1", target=process.arttir, args=[])
# thread_1.start()

# thread_2 = threading.Thread(name="Thread-2", target=process.azalt, args=[])
# thread_2.start()


# thread_1.join()
# thread_2.join()

# print(process.counter)
# print("MainThreadEnd")


executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
threadSubmits = {executor.submit(processManager.sonsuz,) : x for x in range(4)}
futureIterator = concurrent.futures.as_completed(threadSubmits)

