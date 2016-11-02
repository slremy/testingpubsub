'''
    Copyright (c) 2013 Sekou Remy
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    '''

'''
    This program takes nine parameters as command line arguments:
	the duration of the test, 
	
	the step size, 
	the 3 PID constants for the position of the ball
	the 3 PID constants for the angle of the beam
	
    It produces a "fitness value" (higher is better), and provides this response on stdout.
    The value is derived from the step response error for the closed-loop system.
    
    python evaluatePID.py http://IPADDRESS:PORT/ duration STEPSIZE KPball KIball KDball KPbeam KIbeam KDbeam
    
    '''
import web
import timeit
from numpy import sign, power, cos, sin
from collections import deque
import signal
from sys import exit, exc_info, argv
from time import sleep

ref0=[]
ref1=[]

try:
    client = argv[1]
    network = argv[2]
    host = argv[3]
    port = argv[4]
    suffix = argv[5]
    clientport = 0;
    duration= float(argv[6]) if len(argv) > 6 else 200;
    h= float(argv[7]) if len(argv) > 7 else .02;
    KpR= float(argv[8]) if len(argv) > 8 else 6;
    KiR= float(argv[9]) if len(argv) > 9 else 0; #0;
    KdR= float(argv[10]) if len(argv) > 10 else -5.18;
    KpM= float(argv[11]) if len(argv) > 11 else -12.08;
    KiM= float(argv[12]) if len(argv) > 12 else 0;# 0;
    KdM= float(argv[13]) if len(argv) > 13 else -0.4;
    localport = argv[14] if len(argv) > 14 else str(int(port)+1000);
except:
	print exc_info()[0]
	print "syntax is " + argv[0] + " [client] [network] [host] [port] [suffix] duration STEPSIZE KPball KIball KDball KPbeam KIbeam KDbeam"
	exit(0)

#Select process method from the correct client
if client == 'tcp':
    from tcpclient import *
    print "Importing process from tcpclient"
elif client == 'pycurl':
    from pycurlclient import *
    print "Importing process from pycurlclient"
elif client == 'httplib':
    from httplibclient import *
    print "Importing process from httplibclient"
elif client == 'urllib':
    from urllibclient import *
    print "Importing process from urllibclient"
elif client == 'udp':
    from udpclient import *
    print "Importing process from udpclient"
print "Host: %s:%s/" % (host,port)

#strip off trailing slash and http, if present.
host = host.strip('http://').strip('/');

#set up the best clock that can be accessed on this machine
clock = timeit.default_timer;
#get the current time (time the remote was started).
t0 = clock();
t=0

def closeprocess():
	#process(host, port, "/stop?", clientport);
	process(host, port, "/init?", clientport);

def catcher(signum, _):
    #Sekou, you or someone, should convert this to a PID controller (11/8/2014)
    global X, THETA, Y, PHI, t, StateTime, u_x, u_y
    global tcrash, crashed, iteration, mse_x, mse_y
    
    if ref0==[]:return
    # Update the time and iteration number
    iteration += 1

    t1 = clock()-t0
    url = "/u?&value0=%.4f&value1=%.4f&time=%.6f&stime=%.6f&access=8783392" % (u_x,u_y,t,StateTime);

    response=process(host,port,url,clientport);
    tr = clock() - t0;

    if response != "" and ref0 != []:
        X.appendleft( float(response.split()[0]));
        THETA.appendleft( float(response.split()[2]));
        Y.appendleft( float(response.split()[1]));
        PHI.appendleft( float(response.split()[3]));
        StateTime = float(response.split()[4])

        e_x = ref0 - X[0];
        angle_d = AR * (e_x) + BR * (X[0]-X[1]);

        if angle_d > angle_max: angle_d=angle_max; 
        elif angle_d < -angle_max: angle_d=-angle_max; 
        u_x = AM*(angle_d*16 - THETA[0]) + BM * (THETA[0] - THETA[1])

        e_y = ref1 - Y[0];
        angle_d1 = AR * (e_y) + BR * (Y[0]-Y[1]);

        if angle_d1 > angle_max: angle_d1=angle_max; 
        elif angle_d1 < -angle_max: angle_d1=-angle_max; 
        u_y = AM*(angle_d1*16 - PHI[0]) + BM * (PHI[0] - PHI[1])

        #Update the performance parameters
        mse_x = (mse_x * iteration + e_x**2)/(iteration + 1)
        mse_y = (mse_y * iteration + e_y**2)/(iteration + 1)
      
    else:
        print "Communication timed out! ", clock() - t0 
	print "(",ref0, ref1,")", X[-1], Y[-1]


web.config.debug = False;
urls = (
		'/a','remotecontroller',
		'/reset','reset',
		'/stop','closecontroller'
		)

app = web.application(urls, globals())
wsgifunc = app.wsgifunc()
wsgifunc = web.httpserver.StaticMiddleware(wsgifunc)
server = web.httpserver.WSGIServer(("0.0.0.0", int(localport)),wsgifunc)
print "http://%s:%s/" % ("0.0.0.0", localport)

class remotecontroller:
    def GET(self):
        return self.process();
    def POST(self):
        return self.process();
    def process(self):
        global ref0, ref1
        i = web.input();#print i
        (ref0, ref1) = (( float((i.ref0).replace(" ","+")) if hasattr(i, 'ref0') else 0 ), ( float((i.ref1).replace(" ","+")) if hasattr(i, 'ref1') else 0 ))
        #print ref0, ref1 , "<<=== desired"
        f = "%.4f %.4f %.4f %.4f %s" % (X[-1], Y[-1], THETA[-1], PHI[-1], repr(clock()));
        web.header("Content-Type", "text/plain") # Set the Header
        web.header("Access-Control-Allow-Origin", "*") # Set the Header
        web.header("Access-Control-Allow-Credentials", "true") # Set the Header
        return f
        
class reset:
    def GET(self):
        return self.process();
    def POST(self):
        return self.process();
    def process(self):
        global ref0, ref1
        i = web.input();#print i
        (ref0, ref1) = ([],[])
        print ref0, ref1 , "<<=== desired"
        f = "%.4f %.4f %.4f %.4f %s" % (X[-1], Y[-1], THETA[-1], PHI[-1], repr(clock()));
        web.header("Content-Type", "text/plain") # Set the Header
        web.header("Access-Control-Allow-Origin", "*") # Set the Header
        web.header("Access-Control-Allow-Credentials", "true") # Set the Header
        return f
        
def stopper():
    server.stop()
    exit(0);

if __name__ == "__main__":
    (mysignal,myitimer)=(signal.SIGALRM,signal.ITIMER_REAL)
    '''
        (mysignal,myitimer)=(signal.SIGPROF,signal.ITIMER_PROF)
        (mysignal,myitimer)=(signal.SIGVTALRM,signal.ITIMER_VIRTUAL)
        '''
    
    if h < duration/3.0 and h > 0.001:
        signal.signal(mysignal, catcher)
        signal.setitimer(myitimer, h, h)

        try:
            server.start()
        except (KeyboardInterrupt, SystemExit):
            server.stop()
            print exc_info()[0],"Shutting down service"

        #closeprocess();
#return value

