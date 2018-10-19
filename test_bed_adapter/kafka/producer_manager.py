from ..utils.event_hook import EventHook
from .kafka_manager import KafkaManager
import datetime, time
import logging
import uuid


class ProducerManager(KafkaManager):
    def __init__(self, kafka_topic, kafka_host, exclude_internal_topics, client_id, send_messages_asynchronously, avro_helper_key, avro_helper_value, succesfully_sent_message, ssl_config):
        super().__init__(kafka_topic, kafka_host, exclude_internal_topics, avro_helper_key, avro_helper_value, ssl_config)

        self.client_id = client_id
        self.heartbeat_topic = b"system_heartbeat"
        self.send_messages_asynchronously = send_messages_asynchronously

        # The emisor handler will be fired if a message is sent
        self.on_sent = EventHook()

        if succesfully_sent_message and not (kafka_topic == self.heartbeat_topic):
            self.on_sent += succesfully_sent_message

        if (self.send_messages_asynchronously):
            self.producer = self.client_topic.get_producer()
            logging.info("Messages will be send asynchronously")
        else:
            self.producer = self.client_topic.get_sync_producer()
            logging.info("Messages will be send synchronously")

    def send_messages(self, messages:list):
        for i in range(0,len(messages)):
            encoded_message = self.avro_encode(messages[i])
            self.producer.produce(encoded_message["message"], encoded_message["key"])
            # We fire the handler to signify that the message was sent OK
            try:
                self.on_sent.fire(messages[i])
            except:
                pass
        self.producer.stop()

    def avro_encode(self, message):
        message = self.assign_key(message)
        encoded_key = self.avro_helper_key.avro_encode_messages(message["key"])
        encoded_body = self.avro_helper_value.avro_encode_messages(message["message"])
        return {"message":encoded_body, "key":encoded_key}

    def assign_key(self, message):
        # If our message has key we use it, otherwise we use a default one
        if "key" not in list(message.keys()):
            date = datetime.datetime.utcnow()
            date_ms = int(time.mktime(date.timetuple())) * 1000
            # For the default key we set a RFC4122 version 4 compliant GUID
            key = {"distributionID": str(uuid.uuid4()), "senderID": self.client_id, "dateTimeSent": date_ms, "dateTimeExpires": 0, "distributionStatus": "Test", "distributionKind": "Unknown"}
            message["key"] = key
        return message