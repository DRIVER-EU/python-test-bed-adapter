from event_hook import EventHook
from kafka_manager import KafkaManager
from pykafka.exceptions import ConsumerStoppedException
import logging


class ConsumerManager(KafkaManager):
    def __init__(self, kafka_topic, kafka_host, from_off_set, avro_helper_key, avro_helper_value, handle_message):
        super().__init__(kafka_topic, kafka_host, from_off_set, avro_helper_key, avro_helper_value)

        self.simple_consumer = None

        # The emisor handler will be fired if a message is listened
        self.on_message = EventHook()
        if handle_message:
            self.on_message += handle_message

    def listen_messages(self):
        self.simple_consumer = self.client_topic.get_simple_consumer()
        try:
            for message in self.simple_consumer:
                if message is not None:
                    decoded_value, decoded_key = "", ""

                    if self.avro_helper_key:
                        decoded_key = self.avro_helper_key.avro_decode_message(message.partition_key)

                    if self.avro_helper_value:
                        decoded_value = self.avro_helper_value.avro_decode_message(message.value)
                    decoded_message = {"decoded_key": decoded_key, "decoded_value": decoded_value}
                    # We fire the handler to pass the decoded message
                    self.on_message.fire(decoded_message)
        # We do not throw the exception if it occurs because we have externally closed the simple consumer
        except ConsumerStoppedException as e:
            logging.warning("kafka consumer for topic " + str(self.topic) + "was stoped")

    def stop(self):
        if self.simple_consumer:
            self.simple_consumer.stop()
