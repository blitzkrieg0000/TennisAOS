import cv2
import numpy as np
from confluent_kafka import Consumer
import consts

def run_stream_consumer(topic):
    if not topic:
        raise ValueError("topic cannot be empty")
    
    consumer = Consumer({
            'bootstrap.servers': ",".join(["192.168.29.2:9092"]), #consts.KAFKA_BOOTSTRAP_SERVERS
            'group.id': 'test',
            'auto.offset.reset': 'earliest'
        })
    
    consumer.subscribe([topic])
    while True:
        msg = consumer.poll(1)
        if msg is None:
            continue
        if msg.error():
            logging.info("Consumer error: {}".format(msg.error()))
            continue
        
        nparr = np.frombuffer(msg.value(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        cv2.imshow("", cv2.resize(frame, (640, 480)))
        if cv2.waitKey(0) & 0xFF == ord("q"):
            break
    consumer.close()

if __name__=="__main__":
    run_stream_consumer("tenis_saha_1-0")
        