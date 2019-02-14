from ..kafka.consumer_manager import ConsumerManager
from datetime import datetime
import threading
import logging


def milliseconds_since_epoch(date):
    return int((date - datetime(1970, 1, 1)).total_seconds() * 1000)


def millisecond_since_date(date):
    # Get delta time since last update
    dt = datetime.now() - date
    # Convert dt to milliseconds
    return (((dt.days * 24 * 60 * 60 + dt.seconds) * 1000000) + dt.microseconds) / 1000


class TimeService:
    def __init__(self,
                 kafka_system_time_consumer: ConsumerManager):
        # Add handler for system time control messages
        kafka_system_time_consumer.on_message += self.on_system_time_message
        # Time variables
        self.localUpdatedSimTimeAt = datetime.now()
        self.inputUpdatedAt = milliseconds_since_epoch(self.localUpdatedSimTimeAt)
        self.trialTime = milliseconds_since_epoch(self.localUpdatedSimTimeAt)
        self.timeElapsed = 0
        self.trialTimeSpeed = 1.0  # 0 means pause, 1 is real-time
        self.state = "Idle"

        # Create threads
        self.system_time_consumer_thread = threading.Thread(target=kafka_system_time_consumer.listen_messages)
        self.system_time_consumer_thread.setDaemon(True)  # Stop this thread if main thread ends
        self.system_time_consumer_thread.start()

    def stop(self):
        self.system_time_consumer_thread.join()

    def on_system_time_message(self, message):
        # logging.info("system_time message received: " + str(message))
        latency = 0  # self.localUpdatedSimTimeAt - self.updatedAt
        self.localUpdatedSimTimeAt = datetime.now()
        self.inputUpdatedAt = message['decoded_value'][0]['updatedAt']
        self.trialTimeSpeed = message['decoded_value'][0]['timeElapsed']
        self.timeElapsed = message['decoded_value'][0]['trialTimeSpeed']
        self.state = message['decoded_value'][0]['state']
        self.trialTime = message['decoded_value'][0]['trialTime'] + (latency * self.trialTimeSpeed)

    def get_trial_date(self):
        """ Returns UTC date of trial time """
        # Return elapsed if not idle otherwise return date
        elapsed_ms = millisecond_since_date(self.localUpdatedSimTimeAt) * self.trialTimeSpeed
        return datetime.fromtimestamp((self.trialTime + elapsed_ms) / 1000.0) if self.state is not "Idle" else datetime.now()

    def get_trial_elapsed_time(self):
        """ Returns number of milliseconds elapsed since Unix Epoch """
        return self.trialTime + millisecond_since_date(self.localUpdatedSimTimeAt)

    def get_trial_speed(self):
        """ Returns current trial speed """
        return self.trialTimeSpeed
