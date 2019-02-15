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


def get_field_value(message, field, default_value):
    try:
        return message['decoded_value'][0][field]
    except (IndexError, KeyError):
        logging.error("Time service: %s field expected in message but not present, assuming %s" %
                      (field, str(default_value)))
        return default_value


def is_field_present(message, field):
    try:
        check = message['decoded_value'][0][field]
        return True
    except (IndexError, KeyError):
        return False


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
        self.inputUpdatedAt = get_field_value(message, 'updatedAt', self.inputUpdatedAt)
        self.trialTimeSpeed = get_field_value(message, 'trialTimeSpeed', self.trialTimeSpeed)
        self.timeElapsed = get_field_value(message, 'timeElapsed', self.timeElapsed)
        self.state = get_field_value(message, 'state', self.state)
        # TrialTime is special. Rx timestamp is not updated if this field is not present
        if is_field_present(message, 'trialTime'):
            self.localUpdatedSimTimeAt = datetime.now()
            self.trialTime = message['decoded_value'][0]['trialTime'] + (latency * self.trialTimeSpeed)
        else:
            logging.error("Time service: trialTime field expected in message but not present")

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
