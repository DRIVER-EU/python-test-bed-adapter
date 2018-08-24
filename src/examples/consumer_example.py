import logging
logging.basicConfig(level=logging.INFO)
import time
import sys
sys.path += ["..", "../options", "../utils", "../kafka", "../registry"]
from test_bed_options import TestBedOptions
from test_bed_adapter import TestBedAdapter
import json
class ConsumerExample:
    def main(self):
        options_file = open("test_bed_options_example.json", encoding="utf8")
        options = json.loads(options_file.read())
        options_file.close()

        # If you prefer to use a dictionary for the options instead of a file:
        #options = {
        #   "auto_register_schemas": True,
        #   "kafka_host": '127.0.0.1:3501',
        #   "schema_registry": 'http://localhost:3502',
        #   "fetch_all_versions": False,
        #   "from_off_set": True,
        #   "client_id": 'PYTHON TEST BED ADAPTER',
        #   "consume": ["standard_cap"]}

        test_bed_options = TestBedOptions(options)
        test_bed_adapter = TestBedAdapter(test_bed_options)

        # This funcion will act as a handler. It only prints the incoming messages
        handle_message = lambda message: logging.info("\n\n-----\nIncoming message\n-----\n\n" + str(message))

        # Here we add the message to the test bed adapter
        test_bed_adapter.on_message += handle_message

        # We initialize the process (catching schemas and so on) and we listen the messages from the topic standard_cap
        test_bed_adapter.initialize()
        test_bed_adapter.consumer_managers["standard_cap"].listen_messages()



if __name__ == '__main__':
    ConsumerExample().main()
