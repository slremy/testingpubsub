#Revision 2: Added motor saturation speed 
#Revision 3: Cleaned up and added changes that hopefully boost efficiency
#Revision 4: Implemented state propagation by Heun's method for more accuracy
#Revision 5: Cleaned up code by adding string formatting
#Revision 6: Doesn't send velocity data now, and sends smaller  packets.
#Revision 7: Cross Origin Access (you can request data from web pages on different servers).
#       Changed all printing to conform with python3
#       initial floating point modulus (needs to be completed for smooth transitions 0-360-0)
 
#Solve termination problem by set the subthread  daemon = True
#Revision 8: update to add dccp, tcp and udp - Feb 2015
 
from time import sleep
import signal
import timeit
from sys import exit, exc_info, argv
from collections import deque
 
#Simulation time step
h = .02 #Simulation timestep (seconds)
  
try:			#read the listening port from terminal
    port = int(argv[1])
except:
    port = 8080;
 
clock = timeit.default_timer;
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
 
#Set model parameters
m = 0.111;
R = 0.015;
g = -9.8;
L = 1.0;
d = 0.03;
J = 9.99e-6;
H = -m*g*d/L/(J/R*R+m);

#http://www.forkosh.com/mimetex.cgi?P(s)=\frac{-m*g*d/L/(J/R^2+m)}{s^2}
#http://www.forkosh.com/mimetex.cgi?s=\frac{z-1}{zh}
#http://www.forkosh.com/mimetex.cgi?r[n]=2r[n-1]-r[n-2]+Hh^2\theta[n]

Dist =  deque([ (0,0), (0,0), (0,0)],10);
Theta = deque([ (0,0), (0,0), (0,0)],10);
U =     deque([ (0,0), (0,0), (0,0)]);

#http://www.forkosh.com/mimetex.cgi?P(s)=\frac{\Theta(z)}{V_{in}(z)}=\frac{A_2^2z^2}{B_2^2z^2 + B_1z + B_0}

alpha=0.01176
beta=0.58823
#http://www.forkosh.com/mimetex.cgi?P(s)=\frac{\Theta(s)}{V_{in}(s)}=\frac{1}{s(\alpha s+\beta)}
A12=h*h
B12=alpha
B11=(beta*h - 2*alpha)
B10=alpha
P=A12/B12
Q=B11/B12
R=B10/B12
theta_high = 3.14/180.0*(32+20);
r_high = 3.1;


#2.2.6
#http://www.forkosh.com/mimetex.cgi?P(s)=\frac{X(s)}{A(s)}=\frac{-7}{s^2}

A22=-7*h*h
B22=1
B21=-2
B20=1
L=A22/B22
M=B21/B22
N=B20/B22

#Simulation parameters
t0 = clock()
t = 0
u = (0,0);
u_time = t0;
s_time = 0;

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
def updateState(signum, _):
    global Theta, Dist, U, t
    try:
        U.append(u);
        theta0 =  P * U[-1][0] - Q * Theta[-1][0] - R * Theta[-2][0]
        if theta0 > theta_high: theta0 = theta_high
        elif theta0 < -theta_high: theta0 = -theta_high

        theta1 =  P * U[-1][1] - Q * Theta[-1][1] - R * Theta[-2][1]
        if theta1 > theta_high: theta1 = theta_high
        elif theta1 < -theta_high: theta1 = -theta_high

        Theta.append((theta0,theta1));
        x0 =  L * Theta[-1][0]/16.0 - M * Dist[-1][0] - N * Dist[-2][0]; #alpha = theta/16 eqn 2.2.2 EEE490

        if x0 > r_high: x0 = r_high;
        elif x0 < -r_high: x0 = -r_high;

        x1 =  L * Theta[-1][1]/16.0 - M * Dist[-1][1] - N * Dist[-2][1]; #alpha = theta/16 eqn 2.2.2 EEE490

        if x1 > r_high: x1 = r_high;
        elif x1 < -r_high: x1 = -r_high;

        Dist.append((x0,x1));
        t = clock() - t0
    except:
        print(exc_info())
  
 
#////////////////////////////////
 
def initModel_process(data):
    global Dist,Theta,u
    #Could be parsed using urllib!
    #we will assume that all
    t0 = clock() #Time at which the plant received the initialization command from controller
    try:
        dist0 = float(data[1].split("=")[1]);
        dist1 = float(data[2].split("=")[1]);
        theta0 = float(data[3].split("=")[1]);
        theta1 = float(data[4].split("=")[1]);
    except:
        (dist0, dist1, theta0, theta1) = (0,0,0,0)
        
    Dist=deque([ (dist0,dist1) ]*3);
    Theta=deque([ (theta0,theta1) ]*3)
    c_t0 = 0 #Time at which the controller called to initialize the plant
    f = " "	#Feb 11, 2015 "" modified to " " send something to controller to prevent socket timeout problems in contorller side 
    return f
 
def state_process():
    f = "%.4f %.4f %.4f %.4f %.10g" % (Dist[-1][0],Dist[-1][1],Theta[-1][0],Theta[-1][1],t);
    return f
  
def model_process(input):
    global u, u_time, s_time
    data = input.split("&");
    #Could be parsed using urllib!
    #we will assume that all the data are present value0,value1, and time
    try:
        u = (float(data[1].split("=")[1]), #value0
                  float(data[2].split("=")[1])) #value1
        c_t = float(data[3].split("=")[1])

        f = "%.4f %.4f %.4f %.4f %.6f" % (Dist[-1][0],Dist[-1][1],Theta[-1][0],Theta[-1][1],c_t);
    except:
        print(exc_info(), port, "couldn't update the plant", input)
        f = ""
    return f
 
#method that parses the request and sends to the approproate handler
def interpret(whole_data):
    #print whole_data 
    data1 = whole_data.split("]")
    last_complete_packet = data1[len(data1) - 2];
 
    query_string = last_complete_packet.split('?')
 
    datahandler = query_string[0].split('/')[-1]; #print query_string[1]
 
    if datahandler == "init":
        return "["+initModel_process(query_string[1])+"]"
    elif datahandler == "u":
        return "["+model_process(query_string[1])+"]"
    elif datahandler == "state":
        return "["+state_process()+"]"
    elif datahandler == "stop":
        notFinished = False;
    #elif datahandler == "":
    else:
        return "["+"empty"+"]"
 
