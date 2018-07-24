from event_hook import EventHook
from pykafka import KafkaClient
from pykafka.exceptions import ConsumerStoppedException
import datetime, time
import logging
import uuid

class KafkaManager():
    def __init__(self, kafka_topic, kafka_host, from_off_set, avro_helper_key, avro_helper_value):
        self.topic = kafka_topic
        self.avro_helper_key = avro_helper_key
        self.avro_helper_value = avro_helper_value
        self.from_off_set = from_off_set
        self.kafka_host = kafka_host

        # we set up the Kafka client and kafka client topics to obtain consumers and producers from them in the classes
        # that will inherit from this
        self.client = KafkaClient(hosts=self.kafka_host, exclude_internal_topics=self.from_off_set)
        self.client_topic = self.client.topics[kafka_topic]
