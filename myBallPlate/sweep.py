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
filename = "sweep_%s_%s_%s.txt" % (client, network, suffix)
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
    print "Importing process from httplibclient"
elif client == 'ros':
    from rosclient import *
    initialize_handshake(host, port)
    print "Importing process from rosclient"
elif client == 'dweet':
    from dweetclient import *
    initialize_handshake(host, port)
    print "Importing process from dweetclient"
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

ykernel = 'sin'
yamplitude = 1.0
yfrequency = 1.0/100.00
xkernel = 'cos'
xamplitude = 1.0
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
t0_relative=0
F= [.01,.02,.03,.04,.05,.1,.2,.3,.4,.5,1,2,3,4,5];
F= [.01,.02,.03,.04,.05,.06,.07,.08,.083,.09,.093,.1,.103,.11,.12,.15,.17,.2,.3,.4];
F=[0.09, 0.093, 0.1, 0.103, 0.11, 0.12, 0.15, 0.17, 0.2, 0.3, 0.4]
interval_end, interval = 0, -1

#The main control loop
def controlloop(signum, _):
    #Sekou, you or someone, should convert this to a PID controller (11/8/2014)
    global X, THETA, Y, PHI, t, StateTime, u_x, u_y
    global tcrash, crashed, iteration, mse_x, mse_y, interval_end, interval
    
    # Update the time and iteration number
    iteration += 1

    t = clock()-t0
    url = "/u?&value0=%.4f&value1=%.4f&time=%.6f&access=8783392" % (u_x,u_y,t);

    response=process(host,port,url,clientport);
    #time.sleep(1)
    tr = clock() - t0;
    try:
        if len(response) > 20:
            X.appendleft( float(response.split()[0]));
            THETA.appendleft( float(response.split()[2]));
            Y.appendleft( float(response.split()[1]));
            PHI.appendleft( float(response.split()[3]));
            StateTime = float(response.split()[4])

            x_d = ref(t-t0_relative, xkernel,xamplitude, F[interval])
            e_x = x_d - X[0];
            angle_d = AR * (e_x) + BR * (X[0]-X[1]);

            if angle_d > angle_max: angle_d=angle_max; 
            elif angle_d < -angle_max: angle_d=-angle_max; 
            u_x = AM*(angle_d*16 - THETA[0]) + BM * (THETA[0] - THETA[1])

            y_d = ref(t-t0_relative, ykernel, yamplitude, F[interval])
            e_y = y_d - Y[0];
            angle_d1 = AR * (e_y) + BR * (Y[0]-Y[1]);

            if angle_d1 > angle_max: angle_d1=angle_max; 
            elif angle_d1 < -angle_max: angle_d1=-angle_max; 
            u_y = AM*(angle_d1*16 - PHI[0]) + BM * (PHI[0] - PHI[1])

            #Update the performance parameters
            mse_x = (mse_x * iteration + e_x**2)/(iteration + 1)
            mse_y = (mse_y * iteration + e_y**2)/(iteration + 1)
          
            #Write the data to a text file (I know it's ugly)
            fobj.write("%.10g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.10g\t%.10g\n" % (StateTime,X[0],Y[0],THETA[0],PHI[0],StateTime,x_d,y_d,angle_d,angle_d1,mse_x,mse_y,u_x,u_y,tr,StateTime));
        else:
            print "Communication timed out! ", clock() - t0 
            StateTime = float(response);
            fobj.write("%.10g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.10g\t%.10g\n" % (StateTime,float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),tr,StateTime));
    except:
        print response, "<--- this is why it failed"

if __name__ == "__main__":
    url = "/init?&time=0"
    process(host,port,url,clientport)

    #(timer, interrupt)=(signal.ITIMER_PROF, signal.SIGPROF)
    #(timer, interrupt)=(signal.ITIMER_REAL, signal.SIGALRM)
    #signal.signal(interrupt, controlloop)
    #signal.setitimer(timer, h, h)
    thetime=clock()+h
    #Stop program after duration
    print t, interval_end, interval, F[interval]
    while t < dur and crashed == False and interval < len(F)-1:
        
        if thetime < clock():
            thetime=clock()+h
            controlloop(None,None);
        
        if t >= interval_end:
            url = "/init?&time=0"
            process(host,port,url,clientport)
            interval = interval+1;
            t0_relative = t;
            interval_end = t + 10/F[interval];print interval_end, F[interval]


    # Stop timer and plant
    #signal.setitimer(signal.ITIMER_REAL, 0, h)
    signal.setitimer(signal.ITIMER_PROF, 0, h)
    url = "/init?&time=0"
    process(host,port,url,clientport)
    fobj.close()

