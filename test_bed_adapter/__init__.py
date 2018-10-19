from .utils.event_hook import EventHook
from .options.test_bed_options import TestBedOptions
from .kafka.consumer_manager import ConsumerManager
from .kafka.producer_manager import ProducerManager
from .registry.schema_registry import SchemaRegistry
from .registry.schema_publisher import SchemaPublisher
from .kafka.heartbeat_manager import HeartbeatManager
from pykafka.connection import SslConfig
import logging


class TestBedAdapter:
    def __init__(self, test_bed_options: TestBedOptions):

        self.test_bed_options = test_bed_options
        self.schema_registry = SchemaRegistry(test_bed_options)
        self.schema_publisher = SchemaPublisher(test_bed_options)
        self.heartbeat_topic = "system_heartbeat"
        self.heartbeat_interval = test_bed_options.heartbeat_interval
        self.consumer_managers = {}
        self.producer_managers = {}
        self.connected = False

        # If we are using ssl we create the ssl config object
        if self.test_bed_options.use_ssl:
            self.ssl_config = SslConfig(self.test_bed_options.ca_file, self.test_bed_options.cert_file,
                                        self.test_bed_options.key_file, self.test_bed_options.password_private_key)
        else:
            self.ssl_config = None

        # We set up the handlers for the events
        self.on_ready = EventHook()
        self.on_message = EventHook()
        self.on_sent = EventHook()
        self.on_error = EventHook()

    def initialize(self):
        logging.info("Initializing test bed")
        self.schema_registry.start_process()
        self.schema_publisher.start_process()
        self.init_consumers()
        self.init_producers()
        self.init_and_start_heartbeat()
        self.connected = True

        # We emit here by firing the on ready observable.
        self.on_ready.fire()

    def init_consumers(self):
        for topic_name in self.test_bed_options.consume:
            if (topic_name in list(self.schema_registry.values_schema.keys())):
                avro_helper_key = self.schema_registry.keys_schema[topic_name]["avro_helper"]
                avro_helper_value = self.schema_registry.values_schema[topic_name]["avro_helper"]

                # We create a new consumer for this topic. The last input is the callback where we handle the message recieved and decoded from kafka.
                manager = ConsumerManager(bytes(topic_name, 'utf-8'), self.test_bed_options.kafka_host,
                                          self.test_bed_options.exclude_internal_topics,
                                          self.test_bed_options.reset_offset_on_start,
                                          self.test_bed_options.offset_type,
                                          self.test_bed_options.client_id,
                                          avro_helper_key, avro_helper_value,
                                          self.handle_message, self.ssl_config)
                self.consumer_managers[topic_name] = manager
                logging.info("Initialized kafka consumer manager for topic" + topic_name)
            else:
                logging.error("No schema found for topic " + topic_name)

    def init_producers(self):
        if self.heartbeat_topic not in self.test_bed_options.produce:
            self.test_bed_options.produce.append(self.heartbeat_topic)

        for topic_name in self.test_bed_options.produce:
            if (topic_name in list(self.schema_registry.values_schema.keys())):
                avro_helper_key = self.schema_registry.keys_schema[topic_name]["avro_helper"]
                avro_helper_value = self.schema_registry.values_schema[topic_name]["avro_helper"]

                # We create a new producer for this topic. The last input is the callback where we handle the message sent.
                manager = ProducerManager(bytes(topic_name, 'utf-8'), self.test_bed_options.kafka_host,
                                          self.test_bed_options.exclude_internal_topics,
                                          self.test_bed_options.client_id,
                                          self.test_bed_options.send_messages_asynchronously,
                                          avro_helper_key, avro_helper_value,
                                          self.succesfully_sent_message, self.ssl_config)
                self.producer_managers[topic_name] = manager
                logging.info("Initialized kafka producer manager for topic" + topic_name)
            else:
                logging.error("No schema found for topic " + topic_name)

    def init_and_start_heartbeat(self):
        self.heartbeat_manager = HeartbeatManager(self.producer_managers[self.heartbeat_topic], self.heartbeat_interval,
                                                  self.test_bed_options.client_id)
        self.heartbeat_manager.start_heartbeat_async()

    def stop(self):
        # We stop the heatbeat thread
        self.heartbeat_manager.stop()
        # We stop all the kafka listeners
        for manager in list(self.consumer_managers.values()):
            manager.stop()
        self.connected = False

    def handle_message(self, message):
        # We emit the message recieved
        self.on_message.fire(message)

    def succesfully_sent_message(self, message):
        # We emit the message sent
        self.on_sent.fire(message)
