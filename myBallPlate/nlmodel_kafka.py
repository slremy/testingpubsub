# python nlcontroller.py kafka internet dsci002.palmetto.clemson.edu 6667 local_new 3600 0.20 6.09 3.5 -5.18 -12.08 6.58 -0.4
# ip addr for broker = 10.1125.8.197
# sudo tcpdump -i wlan0 -n net 10.125.8.197 -w capture.cap


from nlmodel import *
from pykafka import KafkaClient
from pykafka.common import OffsetType
import logging

#Take arguments to determine file name, port, etc.
try:
    host = argv[1]
    port = int(argv[2])
    topics = argv[3]
    control_action,plant_state = [t(s) for t,s in zip((str,str),topics.split("__"))]
except:
    print(exc_info())
    print("Usage: python nlmodel_kafka.py host port controlaction__plantstate")
    print("e.g. python nlmodel_kafka.py t3.cs.clemson.edu 9898 control_action__plant_state")
    exit(1)

kafka,producer,consumer = None,None,None
control_group = "control_group"
response = ""
old_response = ""

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    global kafka,producer,consumer
    timeout = 150
    server = HOST+":"+str(PORT)

    kafka = KafkaClient(hosts=server)
    
    producer_topic = kafka.topics[plant_state]
    consumer_topic = kafka.topics[control_action]

    producer = producer_topic.get_producer(min_queued_messages=1, max_queued_messages=1)

    consumer = consumer_topic.get_simple_consumer(consumer_group=control_group, auto_offset_reset=OffsetType.LATEST, reset_offset_on_start=True) 
    print "Model's Consumer and SimpleProducer successfully connected and now going to send opneing message..."
    producer.produce(interpret("/state?&]"))


  #  read from the consumer

def read_from_consumer():
	global response, consumer, no_produce
	try:
		response = consumer.consume(block=False).value # block=False ?
	except:
		pass;

 #   write to the producer

def write_to_producer(msg):
	global producer, old_response
	
	if old_response != response:	
		producer.produce(interpret(msg))
		old_response = response

if __name__ == '__main__':

	initialize_handshake(host, port)

	try:
		while 1:
			time = clock()
			while clock() < time + h*.997245:
				read_from_consumer()

			write_to_producer(response)

			updateState("_", "_")
	except (KeyboardInterrupt, SystemExit):
		print exc_info()
		producer.stop()
		consumer.stop()
		print "Shutting down service"