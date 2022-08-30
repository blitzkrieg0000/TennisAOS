import json
import redis
import logging
class RedisManager(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0) # redis
        self.keyTypes = {"string": str, "list": list, "hash": dict}
        self.typeDict = {str : b"str", int : b"int", float: b"float", bytes : b"bytes"}
        self.typeDictReversed = dict(zip(self.typeDict.values(), self.typeDict.keys()))

    def typeMapper(self, x, reverse:bool=False):
        usingDict = {}
        if reverse:
            usingDict = self.typeDictReversed
            x.reverse()
        else:
            usingDict = self.typeDict
        return list(map(lambda item: usingDict[item], x))

    def typeCaster(self, response, types):
        types = self.typeMapper(types, True)
        castList = []
        response.reverse()
        for i, t in enumerate(types):
            item = t(response[i].decode("utf-8")) if t!=bytes else response[i]
            castList.append(item)
        return castList

    def writeValueTypes(func):
        def wrapper(self, *args, **kwargs):
            if isinstance(args[1], list):
                val_types = list(map(lambda x : type(x), args[1]))
                mapped = self.typeMapper(val_types)
                self.r.lpush(args[0]+"_type", *mapped)
            return func(self, *args, **kwargs)
        return wrapper

    @writeValueTypes
    def write(self, key, value):
        if isinstance(value, dict):
            return self.r.hset(name=key, mapping=value)
        if isinstance(value, list):
            return self.r.lpush(key, *value)
        if isinstance(value, str):
            return self.r.set(key, value)
        return None

    def castValueType(func):
        def wrapper(self, *args, **kwargs):
            response = func(self, *args, **kwargs)
            if self.getType(args[0]) == list:
                response_type =self.r.lrange(args[0]+"_type", 0, -1)
                return self.typeCaster(response, response_type)
            return response
        return wrapper

    @castValueType
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

    rm = RedisManager()

    key = "blitz"
    rm.delete(key)
    rm.delete(key+"_type")


    #val = ["value-1", 1, 3.4, b"value-3"]
    val = "asdasd"
    rm.write(key, val)
    response = rm.read(key)

    print(response)