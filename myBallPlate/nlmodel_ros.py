from nlmodel import *
import rospy
from std_msgs.msg import String


def callback(data):
    pub.publish(interpret(data.data))
    


if __name__ == "__main__":
    
    signal.signal(signal.SIGALRM, updateState)
    signal.setitimer(signal.ITIMER_REAL, h, h)
  
    #wait until you can't listen anymore
    rospy.init_node('plant', anonymous=True)

    rospy.Subscriber("control_action", String, callback)
    pub = rospy.Publisher("plant_state", String);#,queue_size=10);

    try:
        # spin() simply keeps python from exiting until this node is stopped
        rospy.spin()
    except (KeyboardInterrupt, SystemExit):
        print exc_info()
        signal.setitimer(signal.ITIMER_REAL, 0, h)
        print "Shutting down service"
