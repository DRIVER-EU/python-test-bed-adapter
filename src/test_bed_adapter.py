from event_hook import EventHook
from test_bed_options import TestBedOptions
from kafka_manager import KafkaManager
from registry.schema_registry import SchemaRegistry
from schema_publisher import SchemaPublisher
from heartbeat_manager import HeartbeatManager
import logging

class TestBedAdapter:
    def __init__(self, test_bed_options: TestBedOptions):

        self.test_bed_options = test_bed_options
        self.schema_registry = SchemaRegistry(test_bed_options)
        self.schema_publisher = SchemaPublisher(test_bed_options)
        self.heartbeat_topic = "system_heartbeat"
        self.heartbeat_interval = test_bed_options.heartbeat_interval
        self.kafka_managers = {}

        # We set up the handlers for the events
        self.on_ready = EventHook()
        self.on_message = EventHook()
        self.on_sent = EventHook()
        self.on_error = EventHook()

    def initialize(self):
        logging.info("Initializing test bed")
        self.schema_registry.start_process()
        self.schema_publisher.start_process()
        self.init_consumers_and_producers()
        self.init_heartbeat()

        # We emit here by firing the on ready observable.
        self.on_ready.fire()

    def init_consumers_and_producers(self):
        logging.info("Initializing kafka producer helpers")
        topics_to_consume_and_produce = list(set((self.test_bed_options.produce + self.test_bed_options.consume)))
        if self.heartbeat_topic not in topics_to_consume_and_produce:
            topics_to_consume_and_produce.append(self.heartbeat_topic)
        self.init_kafka_managers(topics_to_consume_and_produce)
        logging.info("Initialized " + str(len(topics_to_consume_and_produce)) + " producers")

    def init_heartbeat(self):
        heartbeat_manager = HeartbeatManager(self.kafka_managers[self.heartbeat_topic], self.heartbeat_interval, self.test_bed_options.client_id)
        heartbeat_manager.start_heartbeat_async()

    # The last input is the function handler that will be called once a message is recieved or sent
    def init_kafka_managers(self, topics):
        for topic_name in topics:
            logging.info("Initializing Kafka manager for topic " + topic_name)
            if (topic_name in list(self.schema_registry.values_schema.keys())):
                avro_helper_key = self.schema_registry.keys_schema[topic_name]["avro_helper"]
                avro_helper_value = self.schema_registry.values_schema[topic_name]["avro_helper"]

                # We create a new manager for this topic. The last input is the callback where we handle the message recieved and decoded from kafka.
                manager = KafkaManager(bytes(topic_name, 'utf-8'), self.test_bed_options.kafka_host,
                                       self.test_bed_options.from_off_set,
                                       self.test_bed_options.client_id, avro_helper_key, avro_helper_value,
                                       self.succesfully_sent_message,
                                       self.handle_message)
                self.kafka_managers[topic_name] = manager
            else:
                logging.error("No schema found for topic " + topic_name)



    def handle_message(self, message):
        # We emit the message recieved
        self.on_message.fire(message)

    def succesfully_sent_message(self, message):
        # We emit the message sent
        self.on_sent.fire(message)
