import datetime
import logging
import pytz

class Formatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp)
        tzinfo = pytz.timezone("Europe/Istanbul")
        return tzinfo.localize(dt)
        
    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        s = dt.strftime(datefmt)
        #s = dt.isoformat(timespec='milliseconds')
        return s

logger = logging.root
handler = logging.StreamHandler()
handler.setFormatter(Formatter(fmt='%(asctime)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)