import json
import redis
import logging
class RedisManager(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0) # redis
        self.keyTypes = {"string": str, "list": list, "hash": dict}

    def write(self, key, value):
        if isinstance(value, dict):
            return self.r.hset(name=key, mapping=value)
        if isinstance(value, list):
            return self.r.lpush(key, *value)
        if isinstance(value, str):
            return self.r.set(key, value)
        return None

    def read(self, key):
        keyType = self.getType(key)
        if keyType == list:
            return self.r.lrange(key, 0, -1)
        if keyType == dict:
            return self.r.hgetall(key)
        if keyType == str:
            return self.r.get(key)
        return None

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

    def typeMapper(x, reverse:bool=False):
        typeDict = {str : b"str", int : b"int", float: b"float", bytes : b"bytes"}
        if reverse: 
            x.reverse()
            typeDict = dict(zip(typeDict.values(), typeDict.keys()))
        return list(map(lambda item: typeDict[item], x))

    def typeCaster(response, types):
        types = typeMapper(types, True)
        castList = []
        response.reverse()
        for i, t in enumerate(types):
            print(response[i])
            item = t(response[i].decode("utf-8")) if t!=bytes else response[i]
            castList.append(item)
        return castList


    rm = RedisManager()
    
    key = "blitz"
    rm.delete(key)
    rm.delete(key+"type")

    val = ["value-1", 1, 3.4, b"value-3"]
    # val = {"key-1": "value-1", "key-2" : 1,"key-3" : 3.4, "key-4": b"value-3"}
    val_types = list(map(lambda x : type(x), val))


    rm.write(key, val)
    print(typeMapper(val_types))
    rm.write(key+"type", typeMapper(val_types))
    

    response = rm.read(key)
    response_type = rm.read(key+"type")

    print(response, response_type)

        
    response = typeCaster(response, response_type)

    print("response: ", response)

    rm.delete(key)    