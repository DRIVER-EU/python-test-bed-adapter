# python-test-bed-adapter

This is the test-bed adapter for Python: it allows you to easily connect Python 
services to the Apache Kafka test-bed via Python. Although it is specifically 
created for connecting to our [test-bed](https://github.com/DRIVER-EU/test-bed), 
it should work for any Apache Kafka version too.

The implementation is a wrapper around [Pykafka](https://github.com/Parsely/pykafka) 
and [avro-python3](https://avro.apache.org/docs/1.8.2/gettingstartedpython.html) 
offering support for:
- AVRO schema's and messages: both key's and values should have a schema 
as explained [here](https://github.com/DRIVER-EU/avro-schemas).
- Kafka consumer and producer for the test-bed topics.
- Management
  - Heartbeat (topic: connect-status-heartbeat), so you know which clients are online.
  Each time the test-bed-adapter is executed, it starts a heartbeat process to notify
  the its activity to other clients.
  - Configuration (topic: connect-status-configuration), so you can see which 
  topics clients consume and produce.

## Installation
You need to install [Python 3+](https://www.python.org/). 

To install the [PYPI](https://pypi.org/project/python-test-bed-adapter/) package run
 ```pip3 install python-test-bed-adapter```

### Using the Github repo
If you clone the Github repository, to run the examples you will need to install the dependencies
specified on the file 
[requirements.txt](https://github.com/DRIVER-EU/python-test-bed-adapter/blob/master/requirements.txt)
 For that, run
 ```pip3 install -r requirements.txt```
 from the project folder.
 ## Examples and usage
 Check the examples of [consumer](https://github.com/DRIVER-EU/python-test-bed-adapter/blob/master/examples/consumer_example.py)
 and [producer](https://github.com/DRIVER-EU/python-test-bed-adapter/blob/master/examples/producer_example.py).
