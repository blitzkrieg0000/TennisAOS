import concurrent.futures
import time

def UpdateProcess():
   time.sleep(5)

def main():
   
   with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

      threadSubmits = {executor.submit(UpdateProcess) : f"ProcessName_{i}" for i in range(5)}
      
      for future in concurrent.futures.as_completed(threadSubmits):

         message = threadSubmits[future]
        
         try:
            data = future.result()
         except Exception as e:
            print(f"{message} hata hile sonuçlandı: {e}")
         else:
            print(f"{message} tamamlandı.")


if __name__ == '__main__':
   main()
