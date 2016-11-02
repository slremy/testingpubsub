#Revision 2: Added square and sin wave reference input options
#Revision 3: Modified derivative controller to prevent error spikes from crashing the system
#Revision 4: Modified the altitude controller to better track the reference when roll and pitch are nonzero
#Revision 5: Added a controller for x position control
#Revision 6: Tried to clean up and comment code, and stop automatically when it crashes
#Revision 7: Cleaned up and added changes that hopefully boost efficiency
#Revision 8: Added a low pass filter to boost the effectiveness of the PD controller
#Revision 9: Removed plotting. Changed the target trajectories. Almost removed all logging.
#Revision 10: Improved the x-position controller by relaxing the assumption that T is constant
#Revision 11: Improved attitude controller
#Revision 12: Made the code more robust by adding try catch blocks and stopping it when it crashes
#Revision 13: Discretized angle controllers using the Tustin Transform 
#Revision 14: Added lead compensators for phi and psi controllers
#Revision 15: Removed all logging. Now writes output to files. 
#Revision 16: Writes control inputs to files, and takes an input file name for logging
#Revision 17: Added a y position controller and performance metrics
#Revision 18: Restructured code so we can know why it is crashing
#Revision 19: Added other protocols
#Revision 20: Sends and receives less data. Now does not read and log velocity or plant time stamp.
#Revision 21: You now have to input the network conditions (i.e., localhost, ethernet, or wireless) for your argument.
#Revision 22: Made many more changes, which I forgot
#Revision 23: Attempting to tune lead compensators for better response
#Revision 24: Changed the way the user passes in arguments and added additional constraints on inputs
#Revision 25: Low pass filter the position errors before passing through the PD controller

import time
import timeit
import signal
from sys import exit, exc_info, argv
from math import sin, cos, sqrt, asin, isnan, isinf, pi
from collections import deque
from references import *
#http://www.forkosh.com/mimetex.cgi?P(s)=\frac{\alpha_2z^2+\alpha_1z+\alpha_0}{\beta_2z^2+\beta_1z+\beta_0}
#http://www.forkosh.com/mimetex.cgi?s=\frac{z-1}{zh}

#Take arguments to determine file name, port, etc.
try:
    client = argv[1]
    host = argv[2]
    port = argv[3]
    dur= float(argv[4]) if len(argv) > 4 else 3 * 3600;
    h= float(argv[5]) if len(argv) > 5 else .02;
except:
	print exc_info()
	print "Usage: remotecontroller [client(udp,tcp,dccp,...)] [host] [port] duration"
	exit(1)
print dur, h
#Select process method from the correct client
from pycurlclient import *
initialize_handshake(host, port)
print "Importing process from pycurlclient"
print "Host: %s:%s/" % (host,port)
 

#strip off trailing slash and http, if present.
host = host.strip('http://').strip('/');

ykernel = 'butterfly2'
yamplitude = 2.0
yfrequency = 1.0/100.00
psikernel = 'butterfly1'
psiamplitude = 0*pi/180
psifrequency = 1.0/125.0
xkernel = 'butterfly1'
xamplitude = 2.0
xfrequency = 1.0/100.00


clock = timeit.default_timer;

t0 = clock();
t=0

#The main control loop
def controlloop(signum, _):
    global t
    try:
            t = clock()-t0
            x_d = ref(t, xkernel, xamplitude, xfrequency)
            y_d = ref(t, ykernel, yamplitude, yfrequency)
            url = "/a?&ref0=%.4f&ref1=%.4f&access=8783392" % (x_d,y_d);
            response=process(host,port,url,0);
            url = "/a?&ref0=%.4f&ref1=%.4f&access=8783392" % (-x_d,y_d);
            response=process(host,str(int(port)+1),url,0);
    except:
        print response, "<--- this is why it failed"

if __name__ == "__main__":
    url = "/reset?&time=0"
    process(host,port,url,0)

    #(timer, interrupt)=(signal.ITIMER_PROF, signal.SIGPROF)
    (timer, interrupt)=(signal.ITIMER_REAL, signal.SIGALRM)
    signal.signal(interrupt, controlloop)
    signal.setitimer(timer, h, h)
  
    #Stop program after duration
    while t < dur:
        time.sleep(1)
    
    # Stop timer and plant
    signal.setitimer(interrupt, 0, h)

