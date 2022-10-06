
import time
import uuid

import hashlib
tic = time.time()
unique = int.from_bytes(hashlib.md5(str(time.time()).encode("utf-8")).digest(), "little")
toc = time.time()
manuel = toc-tic
print(manuel, unique)


tic = time.time()
unique = str(uuid.uuid4())
toc = time.time()
lib = toc-tic
print(lib, unique)


if manuel > lib:
    print("lib")
else:
    print("manuel")



