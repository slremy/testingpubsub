import paho.mqtt.client as mqtt
from nlmodel import *


#Take arguments to determine file name, port, etc.
try:
    host = argv[1]
    port = int(argv[2])
    topics = argv[3]
    control_action,subQosLevel,plant_state,pubQosLevel = [t(s) for t,s in zip((str,int,str,int),topics.split("__"))]
except:
    print(exc_info())
    print("Usage: python nlmodel_mqtt.py host port controlaction__subQOS__plantstate__pubQOS")
    print("e.g. python nlmodel_mqtt.py iot.eclipse.org 1883 uisgroup/control_action0__1__uisgroup/plant_state__1")
    exit(1)

def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mosq, obj, level, string):
    print(string)

def on_connect(mosq, obj, rc):
    print("Subscribing")
    modelclient.subscribe(control_action, subQosLevel)
    print("rc: " + str(rc))
    modelclient.publish(plant_state,interpret("/state?&]"),pubQosLevel);

def on_message(mosq, obj, msg):
    #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    modelclient.publish(plant_state,interpret(msg.payload),pubQosLevel);

def on_publish(mosq, obj, mid):
    #print("mid: " + str(mid))
    pass

try:
    modelclient = mqtt.Client()
    # Assign event callbacks
    modelclient.on_message = on_message
    modelclient.on_connect = on_connect
    modelclient.on_publish = on_publish
    modelclient.on_subscribe = on_subscribe
except :
    print "Device connection failed"

if __name__ == '__main__':
    #connect to a MQTT broker
    modelclient.connect(host, port, 60)
    signal.signal(signal.SIGALRM, updateState)
    signal.setitimer(signal.ITIMER_REAL, h, h)
    
    notFinished = True
    #wait until you can't listen anymore
    while notFinished:
        try:
            modelclient.loop();
    
        except (KeyboardInterrupt, SystemExit):
            notFinished = False
            signal.setitimer(signal.ITIMER_REAL, 0, h)
            print(exc_info())
            print("Shutting down service")
