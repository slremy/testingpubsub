from re import search
import paho.mqtt.client as mqtt

control_action = "uisgroup/control_action"
plant_state = "uisgroup/plant_state"
pubQosLevel = 1
subQosLevel = 1
state = ""

def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mosq, obj, level, string):
    print(string)

def on_connect(mosq, obj, rc):
    print("Subscribing")
    mosq.subscribe(plant_state, subQosLevel)
    print("rc: " + str(rc))

def on_message(mosq, obj, msg):
    global state
    state = msg.payload
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(mosq, obj, mid):
    #print("mid: " + str(mid))
    pass

def on_disconnect(pahoClient, obj, rc):
    print "Disconnected"

try:
    controllerclient = mqtt.Client()
    # Assign event callbacks
    controllerclient.on_message = on_message
    controllerclient.on_connect = on_connect
    controllerclient.on_log = on_log
    controllerclient.on_publish = on_publish
    controllerclient.on_subscribe = on_subscribe
    controllerclient.on_disconnect = on_disconnect
except Exception, err:
    print("Device connection failed", "Error thrown: %s\n" % err)

def initialize_handshake(HOST, PORT): 
    #connect to a [public] MQTT broker
    controllerclient.connect(HOST, PORT, 60);print "connected",HOST, PORT


def process(HOST, PORT, GET,client_socketport=None):
    global controllerclient
    try:
        controllerclient.loop();
        controllerclient.publish(control_action, GET, pubQosLevel);
        response = state
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
    except Exception, err:
        print("Error thrown: %s\n" % err)
        response = (GET.split("time=")[1]).split("&")[0]
    return response


if __name__ == '__main__':
	initialize_handshake(None, None)
	print process(None, None, "/init")
