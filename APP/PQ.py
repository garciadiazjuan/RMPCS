import heapq

class PQ:
    def __init__(self):
        self._queue = []
        self._index = 0  
    
    def push(self, item, priority):
        heapq.heappush(self._queue, (priority, self._index, item))
        self._index += 1
    
    def pop(self):
        return heapq.heappop(self._queue)[-1]
    
    def is_empty(self):
        return len(self._queue) == 0