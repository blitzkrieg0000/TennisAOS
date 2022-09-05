from concurrent import futures
import multiprocessing

class Test():
    def __init__(self):
        self.counter = 0
    
    def islem(self, i):
        for _ in range(10000000):
            if i%2==0:
                self.counter = 1+self.counter
            else:
                self.counter = -1+self.counter


test = Test()
executer = futures.ThreadPoolExecutor(5)
submits = {executer.submit(test.islem, i) : i for i in range(2)}
futureIterator = futures.as_completed(submits)

for future in futureIterator:
    if future.done():
        print(f"{submits[future]} is done\n")


print(test.counter)