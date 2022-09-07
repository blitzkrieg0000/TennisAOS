KAFKA_BOOTSTRAP_SERVERS = ["broker:9092"]
TOPICS_NUM_PARTITION = 1
TOPICS_IGNORE_SET = set(["__consumer_offsets"])
EXCEPT_PREFIX = [''] # Unique olması gereken topicler için kullanılır.