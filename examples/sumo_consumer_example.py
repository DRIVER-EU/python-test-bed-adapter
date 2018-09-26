#!/usr/bin/env python3
import time
import sys
import queue
import threading
import logging
logging.basicConfig(level=logging.INFO)
sys.path += [".."]
from test_bed_adapter.options.test_bed_options import TestBedOptions
from test_bed_adapter import TestBedAdapter

class ConsumerExample:
    def __init__(self):
        self._queue = queue.Queue()

    def addToQueue(self, message):
        self._queue.put(message)

    def main(self):
        options = {
           "auto_register_schemas": True,
           "schema_folder": 'data/schemas',
           # "kafka_host": 'driver-testbed.eu:3501',
           # "schema_registry": 'http://driver-testbed.eu:3502',
           "kafka_host": '127.0.0.1:3501',
           "schema_registry": 'http://localhost:3502',
           "fetch_all_versions": False,
           "from_off_set": True,
           "client_id": 'PYTHON TEST BED ADAPTER',
           "consume": ["sumo_SumoConfiguration", "system_timing"]}

        test_bed_adapter = TestBedAdapter(TestBedOptions(options))
        test_bed_adapter.on_message += self.addToQueue

        test_bed_adapter.initialize()
        threads = []
        for topic in options["consume"]:
            threads.append(threading.Thread(target=test_bed_adapter.consumer_managers[topic].listen_messages))
            threads[-1].start()
        while True:
            message = self._queue.get()
            logging.info("\n\n-----\nHandling message\n-----\n\n" + str(message))




if __name__ == '__main__':
    ConsumerExample().main()
