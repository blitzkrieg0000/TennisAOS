import json
import pickle
import redis

class RedisManager(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='redispool.default.svc.cluster.local', port=6379, db=0)
        self.keyTypes = {"list":"L", "hash": "D", "string": "J"}

    def write(self, key, value, val_type=None):
        if val_type=="L":
            #list
            return self.r.lpush(key, *value)
        if val_type=="D":
            #hash
            return self.r.hset(name=key, mapping=value)
        if val_type=="J":
            #string
            value = json.dumps(value)
            return self.r.set(key, value)
        return self.r.set(key, value)

    def read(self, key, val_type=None):
        if val_type=="L":
            #list
            return self.r.lrange(key, 0, -1)
        if val_type=="D":
            #hash
            return self.r.hgetall(key)
        if val_type=="J":
            #string
            val = self.r.get(key)
            logging.info(val)
            return json.loads(val.decode("utf-8"))
        return self.r.get(key)

        return self.r.get(key)

    def addToDict(self, ikey, key, value):
        return self.r.hset(ikey, key, mapping=value)

    def delete(self, key):
        return self.r.delete(key)

    def setExpire(self, key, exptime):
        return self.r.expire(key, exptime)
    
    def isExist(self, key):
        return self.r.exists(key)

    def getType(self, key):
        keyType = self.r.type(key).decode("utf-8")
        return self.keyTypes.get(keyType, "None")


if __name__ == "__main__":
    rm = RedisManager()
    
    key = "surname"
    ty = rm.getType(key)
    logging.info(ty)

    #del_val = rm.delete(key)
    rm.setExpire(key, 5)
    if rm.isExist(key):
        logging.info("EXIST")
        val = rm.read(key)
    else:
        logging.info("WRITING")
        val = rm.write(key, 5)
    
    logging.info(val)