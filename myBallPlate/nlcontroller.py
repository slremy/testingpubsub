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
    network = argv[2]
    host = argv[3]
    port = argv[4]
    suffix = argv[5]
    clientport = 0;
    dur= float(argv[6]) if len(argv) > 6 else 3 * 3600;
    h= float(argv[7]) if len(argv) > 7 else .02;
    KpR= float(argv[8]) if len(argv) > 8 else -.312-1;
    KiR= float(argv[9]) if len(argv) > 9 else 0;
    KdR= float(argv[10]) if len(argv) > 10 else 1.299;
    KpM= float(argv[11]) if len(argv) > 11 else 5.79;
    KiM= float(argv[12]) if len(argv) > 12 else 0;
    KdM= float(argv[13]) if len(argv) > 13 else .22;
except:
	print exc_info()
	print "Usage: nlcontroller_current [client(udp,tcp,dccp,...)] [network(eth, wifi)] [host] [port] [suffix] duration STEPSIZE KPball KIball KDball KPbeam KIbeam KDbeam"
	exit(1)
 
#Log data to the correct file
filename = "%s_%s_%s.txt" % (client, network, suffix)
print "Logging data to %s" % filename
fobj = open("%s" % filename, 'w')
  
#Select process method from the correct client
if client == 'tcp':
    from tcpclient import *
    initialize_handshake(host, port)
    print "Importing process from tcpclient"
if client == 'dccp':
    from dccpclient import *
    initialize_handshake(host, port)
    print "Importing process from dccpclient"
elif client == 'pycurl':
    from pycurlclient import *
    initialize_handshake(host, port)
    print "Importing process from pycurlclient"
elif client == 'httplib':
    from httplibclient import *
    initialize_handshake(host, port)
    print "Importing process from httplibclient"
elif client == 'httpman':
    from httpmanualclient import *
    initialize_handshake(host, port)
    print "Importing process from httpmanualclient"
elif client == 'ros':
    from rosclient import *
    initialize_handshake(host, port)
    print "Importing process from rosclient"
elif client == 'dweet':
    from dweetclient import *
    initialize_handshake(host, port)
    print "Importing process from dweetclient"
elif client =='kafka':
    from kafkaclient import *
    initialize_handshake(host, port)
    print "Importing process from kafka client"
elif client == 'mqtt':
    from mqttclient import *
    initialize_handshake(host, port)
    print "Importing process from mqttclient"
elif client == 'urllib':
    from urllibclient import *
    initialize_handshake(host, port)
    print "Importing process from urllibclient"
elif client == 'udp':
    from udpclient import *
    print "Importing process from udpclient"
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

u_max=20;
CumulativeError = 0

X =		deque([ 0, 0, 0],3);
THETA = deque([ 0, 0, 0],3);
Y =	deque([ 0, 0, 0],3);
PHI = deque([ 0, 0, 0],3);
StateTime = 0;
u_x=0;u_y=0;
#Performance parameters
iteration = 0 #Keep track of loop iterations
mse_x = 0 #Mean squared error in x
mse_y = 0 #Mean squared error in y
mse_z = 0 #Mean squared error in z
tcrash = float('inf') #Time the program crashed. If it didn't crash, this is infinite
crashed = False #If the program crashed

angle_max = 3.14/180.0*(32+20)
AR= KpR;
BR= KdR/h;

AM= KpM;
BM= KdM/h;
#print AR,BR,AM,BM
clock = timeit.default_timer;

t0 = clock();
t=0

#The main control loop
def controlloop(signum, _):
    #Sekou, you or someone, should convert this to a PID controller (11/8/2014)
    global X, THETA, Y, PHI, t, StateTime, u_x, u_y
    global tcrash, crashed, iteration, mse_x, mse_y
    
    # Update the time and iteration number
    iteration += 1

    t = clock()-t0
    url = "/u?&value0=%.4f&value1=%.4f&time=%.6f&access=8783392" % (u_x,u_y,t);

    response=process(host,port,url,clientport);
    tr = clock() - t0;
    try:
        if len(response) > 20:
            X.appendleft( float(response.split()[0]));
            THETA.appendleft( float(response.split()[2]));
            Y.appendleft( float(response.split()[1]));
            PHI.appendleft( float(response.split()[3]));
            StateTime = float(response.split()[4])

            x_d = ref(t,xkernel ,xamplitude ,xfrequency)
            e_x = x_d - X[0];
            angle_d = AR * (e_x) + BR * (X[0]-X[1]);

            if angle_d > angle_max: angle_d=angle_max; 
            elif angle_d < -angle_max: angle_d=-angle_max; 
            u_x = AM*(angle_d*16 - THETA[0]) + BM * (THETA[0] - THETA[1])

            y_d = ref(t,ykernel,yamplitude,yfrequency)
            e_y = y_d - Y[0];
            angle_d1 = AR * (e_y) + BR * (Y[0]-Y[1]);

            if angle_d1 > angle_max: angle_d1=angle_max; 
            elif angle_d1 < -angle_max: angle_d1=-angle_max; 
            u_y = AM*(angle_d1*16 - PHI[0]) + BM * (PHI[0] - PHI[1])

            #Update the performance parameters
            mse_x = (mse_x * iteration + e_x**2)/(iteration + 1)
            mse_y = (mse_y * iteration + e_y**2)/(iteration + 1)
          
            #Write the data to a text file (I know it's ugly)
            fobj.write("%.10g\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.10g\t%.10g\n" % (StateTime,X[0],Y[0],THETA[0],PHI[0],t,x_d,y_d,angle_d,angle_d1,mse_x,mse_y,u_x,u_y,tr,StateTime));
        else:
            print "Communication timed out! ", clock() - t0 
            StateTime = float(response);
            fobj.write("%.10g\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.10g\t%.10g\n" % (StateTime,float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),tr,StateTime));
    except:
        print response, "<--- this is why it failed"

if __name__ == "__main__":
    url = "/init?&time=0"
    process(host,port,url,clientport)

    #(timer, interrupt)=(signal.ITIMER_PROF, signal.SIGPROF)
    (timer, interrupt)=(signal.ITIMER_REAL, signal.SIGALRM)
    signal.signal(interrupt, controlloop)
    signal.setitimer(timer, h, h)
  
    #Stop program after duration
    while t < dur and crashed == False:
        pass
  
    # Stop timer and plant
    #signal.setitimer(signal.ITIMER_REAL, 0, h)
    signal.setitimer(signal.ITIMER_PROF, 0, h)
    url = "/init?&time=0"
    process(host,port,url,clientport)
    fobj.close()

