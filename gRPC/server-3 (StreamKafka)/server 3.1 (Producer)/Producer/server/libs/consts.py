KAFKA_BOOTSTRAP_SERVERS = ["brokerpool.default.svc.cluster.local:9092"]
TOPICS_NUM_PARTITION = 1
TOPICS_IGNORE_SET = set(["__consumer_offsets", "_schemas", "_confluent-ksql-default__command_topic", "default_ksql_processing_log", "quickstart-config", "quickstart-offsets", "quickstart-status"])
EXCEPT_PREFIX = ['__consumer_offsets', ] # Unique olması gereken topicler için kullanılır.
THREAD_PREFIX = "streaming_thread_"