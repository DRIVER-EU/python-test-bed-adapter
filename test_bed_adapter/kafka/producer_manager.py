from ..utils.event_hook import EventHook
from .kafka_manager import KafkaManager
import datetime, time
import uuid


class ProducerManager(KafkaManager):
    def __init__(self, kafka_topic, kafka_host, exclude_internal_topics, client_id, avro_helper_key, avro_helper_value, succesfully_sent_message, ssl_config):
        super().__init__(kafka_topic, kafka_host, exclude_internal_topics, avro_helper_key, avro_helper_value, ssl_config)

        self.client_id = client_id
        self.heartbeat_topic = b"system_heartbeat"

        # The emisor handler will be fired if a message is sent
        self.on_sent = EventHook()

        if succesfully_sent_message and not (kafka_topic == self.heartbeat_topic):
            self.on_sent += succesfully_sent_message

    def send_messages(self,json_message):
        if "messages" in list(json_message.keys()):
            messages = json_message["messages"]

            date = datetime.datetime.utcnow()
            date_ms = int(time.mktime(date.timetuple())) * 1000

            # If our message has key we use it, otherwise we use a default one
            if "key" in list(json_message.keys()):
                key = json_message["key"]
            else:
                # For the default key we set a RFC4122 version 4 compliant GUID
                key = {"distributionID": str(uuid.uuid4()), "senderID": self.client_id, "dateTimeSent": date_ms, "dateTimeExpires": 0, "distributionStatus": "Test", "distributionKind": "Unknown"}

            encoded_message = self.avro_helper_value.avro_encode_messages(messages)
            encoded_key = self.avro_helper_key.avro_encode_messages(key)

            with self.client_topic.get_sync_producer() as self.producer:
                self.producer.produce(encoded_message, encoded_key)
                # We fire the handler to signify that the message was sent OK
                try:
                    self.on_sent.fire(json_message)
                except:
                    pass
                self.producer.stop()

