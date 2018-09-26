#!/usr/bin/env python3
import os
import sys
import queue
import datetime
import threading
from argparse import ArgumentParser
import json
import logging
logging.basicConfig(level=logging.INFO)
sys.path += [os.path.join(os.path.dirname(__file__), "..")]
from test_bed_adapter.options.test_bed_options import TestBedOptions
from test_bed_adapter import TestBedAdapter
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    import edgesInDistricts
    import sumolib
    import traci
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

def get_options():
    argParser = ArgumentParser()
    argParser.add_argument("--affected-area", dest="area",
                     default="AffectedArea.json", help="affected area definition", metavar="FILE")
    argParser.add_argument("--aggregated-output", dest="aggregatedOutput",
                     default="edgesOutput.xml", help="the file name of the edge-based output generated by SUMO", metavar="FILE")
    argParser.add_argument("--configuration", dest="config",
                     default="Configuration.json", help="configuration definition", metavar="FILE")
    argParser.add_argument("--fcd-output", dest="fcdOutput",
                     default="fcd.output", help=" the file name of the fcd output generated by SUMO", metavar="FILE")
    argParser.add_argument("--network-file", dest="netfile",
                     default="acosta_buslanes.net.xml", help="network file name", metavar="FILE")
    argParser.add_argument("--static-jsonOutput",  action="store_true", dest="staticJsonOutput",
                     default=False, help="write SUMO's static outputs in JSON format")
    argParser.add_argument("--update-configuration", dest="update",
                     default="UpdateConfiguration.json", help="configuration update definition", metavar="FILE")
    argParser.add_argument("--nogui", action="store_true",
                         default=False, help="run the command-line version of sumo")
    argParser.add_argument("--duration-statistics", action="store_true",          # ?: how to send this to the server?
                         default=False, help="enable statistics on vehicle trips")
    argParser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                     default=False, help="tell me what you are doing")
    options = argParser.parse_args()
    return options


class SumoAdapter:
    def __init__(self):
        self._options = get_options()
        self._queue = queue.Queue()
        self._net = None
        self._simTime = None
        self._deltaT = None
        self._config = None

    def addToQueue(self, message):
        self._queue.put(message['decoded_value'][0])

    def handleConfig(self, config):
        self._config = config
        self._simTime = config["begin"]
        if self._options.nogui:
            sumoBinary = sumolib.checkBinary('sumo')
        else:
            sumoBinary = sumolib.checkBinary('sumo-gui')
        try:
            traci.start([sumoBinary, "-S", "-Q",
                                     "-c", config["configFile"],
                                     "--fcd-output", self._options.fcdOutput, 
                                     "--device.fcd.period",str(config["singleVehicle"]),  # todo: add an option for the period
                                     ], numRetries=3)
            self._deltaT = traci.simulation.getDeltaT() * 1000
            for file in sumolib.xml.parse(config["configFile"], 'net-file'):
                netfile = os.path.join(os.path.dirname(config["configFile"]), file.value)
                print (netfile)
            self._net = sumolib.net.readNet(netfile)
        except traci.exceptions.FatalTraCIError as e:
            print(e)

    def handleTime(self, time):
        trialTime = time["trialTime"]
        print(datetime.datetime.fromtimestamp(trialTime / 1000.))
        while self._net is not None and trialTime > self._simTime and self._simTime < self._config["end"]:
            traci.simulationStep()
            self._simTime += self._deltaT

    def main(self):
        testbed_options = {
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

        test_bed_adapter = TestBedAdapter(TestBedOptions(testbed_options))
        test_bed_adapter.on_message += self.addToQueue

        test_bed_adapter.initialize()
        threads = []
        for topic in testbed_options["consume"]:
            threads.append(threading.Thread(target=test_bed_adapter.consumer_managers[topic].listen_messages))
            threads[-1].start()
        while True:
            message = self._queue.get()
            logging.info("\n\n-----\nHandling message\n-----\n\n" + str(message))
            if "configFile" in message:
                self.handleConfig(message)
            elif "trialTime" in message:
                self.handleTime(message)




if __name__ == '__main__':
    SumoAdapter().main()
