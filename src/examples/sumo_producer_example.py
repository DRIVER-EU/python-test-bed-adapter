import unittest
import sys
import json
import os
sys.path += ["..", "../options", "../utils", "../kafka", "../registry"]
from test_bed_options import TestBedOptions
from test_bed_adapter import TestBedAdapter

import logging
logging.basicConfig(level=logging.INFO)

class ProducerExample:

    def main(self):
        options = {
            "auto_register_schemas": True,
            "schema_folder": 'sumo_schemas',
            # "kafka_host": 'driver-testbed.eu:3501',
            # "schema_registry": 'http://driver-testbed.eu:3502',
            "kafka_host": '127.0.0.1:3501',
            "schema_registry": 'http://localhost:3502',
            "fetch_all_versions": False,
            "from_off_set": True,
            "client_id": 'PYTHON TEST BED ADAPTER',
            "produce": ["sumo_configuration"]}

        test_bed_options = TestBedOptions(options)
        test_bed_adapter = TestBedAdapter(test_bed_options)


        #We load a test message from file
        message_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"sample_messages", "Configuration.json")
        example_message_file = open(message_path, encoding="utf-8")
        message_json = json.loads(example_message_file.read())
        example_message_file.close()
        message = {"messages":message_json}


        # This funcion will act as a handler. It only prints the message once it has been sent
        message_sent_handler = lambda message : logging.info("\n\n------\nmessage sent:\n------\n\n" + str(message))

        # Here we add the message to the test bed adapter
        test_bed_adapter.on_sent += message_sent_handler

        test_bed_adapter.initialize()
        test_bed_adapter.producer_managers["sumo_configuration"].send_messages(message)

if __name__ == '__main__':
    ProducerExample().main()
