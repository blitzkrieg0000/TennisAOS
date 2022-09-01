import pickle
import redis

class RedisManager(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='redis', port=6379, db=0) # redis
        self.keyTypes = {"string": str, "list": list, "hash": dict, "bytes": bytes}

    def write(self, key, value):
        if isinstance(value, dict):
            return self.r.hset(name=key, mapping=value)
        if isinstance(value, list):
            return self.r.lpush(key, *value)
        if isinstance(value, str):
            return self.r.set(key, value)
        if isinstance(value, bytes):
            return self.r.set(key, value)

        return None

    def read(self, key):
        val = None
        keyType = self.getType(key)
        if keyType == list:
            val =  self.r.lrange(key, 0, -1)[::-1]
        if keyType == dict:
            val = self.r.hgetall(key)
        if keyType == str:
            val = self.r.get(key)
        if keyType == bytes:
            val = self.r.get(key)

        return val

    def addToDict(self, ikey, key, value):
        return self.r.hset(ikey, key, mapping=value)

    def delete(self, key):
        return self.r.delete(key)

    def setExpire(self, key, exptime):
        return self.r.expire(key, exptime)
    
    def isExist(self, key):
        return self.r.exists(key)

    def getType(self, key):
        return self.keyTypes.get(self.r.type(key).decode("utf-8"), None)


if __name__ == "__main__":

    rm = RedisManager()

    key = "blitz"
    rm.delete(key)

    val = "that byte"
    bval = pickle.dumps(val)
    rm.write(key, bval)
    response = rm.read(key)
    print(response)