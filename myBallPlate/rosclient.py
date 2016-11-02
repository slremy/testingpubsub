#version 1:
from re import search
import rospy
from std_msgs.msg import String
from sys import exit

pub = rospy.Publisher('control_action', String);#,queue_size=10);
state = ""
def callback(data):
    global state
    state = data.data

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    rospy.init_node('controller', anonymous=True)
    rospy.Subscriber('plant_state', String, callback)

def process(HOST, PORT, GET,client_socketport=None):
    if rospy.is_shutdown():
       exit(0);

    try:
        pub.publish(GET+"&]")
#        print "send : "+GET
        response=state
#        response = rospy.wait_for_message('plant_state', String, timeout=.150).data
#        print "response : "+response
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
    except Exception, err:
        rospy.logwarn("[Warning] in ROS client send and receive :%s\n " % err)
        response = (GET.split("time=")[1]).split("&")[0]
    return response

if __name__ == "__main__":
    initialize_handshake(None, None);
    print process(None, None, "/init");
