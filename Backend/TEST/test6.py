import itertools
import queue



q = queue.deque()
[q.appendleft(None) for i in range(0,5)]

q.pop()

for i in range(0, 5):
    print(q[i])
