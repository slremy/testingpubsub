from re import search
from pykafka import KafkaClient
from pykafka.common import OffsetType
import logging
kafka,producer,consumer = None,None,None
control_action = "control_action" 
plant_state = "plant_state"
plant_group = "plant_group"

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    global kafka,producer,consumer
    timeout = 150
    server = HOST+":"+str(PORT)
    
    kafka = KafkaClient(server)
    
    producer_topic = kafka.topics[control_action]
    consumer_topic = kafka.topics[plant_state]

    producer = producer_topic.get_producer(min_queued_messages=1, max_queued_messages=1)

    consumer = consumer_topic.get_simple_consumer(consumer_group=plant_group, auto_offset_reset=OffsetType.LATEST, reset_offset_on_start=True)

    print "Client's Consumer and SimpleProducer successfully connected..."

def process(HOST, PORT, GET,client_socketport=None):
    global producer,consumer
    try:
    	response = consumer.consume(block=False).value # This should not block but it fails otherwise
    	producer.produce(GET)# + "&]") 
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
    except Exception, err:
        consumer.commit_offsets() # Not 100% about this (IF SOMETHING GOES WRONG LOOK HERE)
        print("[Warning] in kafka client send and receive :%s\n " % err)
        response = (GET.split("time=")[1]).split("&")[0]
    return response

if __name__ == "__main__":
    initialize_handshake("dsci002.palmetto.clemson.edu", 6667);
    print process(None, None, "/init");