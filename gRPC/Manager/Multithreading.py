import concurrent.futures
import time

def UpdateProcess(i):
   time.sleep(10)
   print(f"Bitti {i}")
   

def main():
   
   threadIterators = []

   executor = concurrent.futures.ThreadPoolExecutor(max_workers=5) 


   threadSubmits = {executor.submit(UpdateProcess, i) : f"ProcessName_{i}" for i in range(2)}
   threadIterator = concurrent.futures.as_completed(threadSubmits)
   threadIterators.append(threadIterator)

   
   threadSubmits = {executor.submit(UpdateProcess, i) : f"ProcessName_{i}" for i in range(2, 6)}
   threadIterator = concurrent.futures.as_completed(threadSubmits)
   threadIterators.append(threadIterator)
   

   print("Bekleniyor.")

   for iterator in threadIterators:
      for future in iterator:
         pass #print(future.done())


if __name__ == '__main__':
   main()