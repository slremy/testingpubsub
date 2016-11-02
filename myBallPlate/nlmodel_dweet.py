#version 2:
from nlmodel import *

import json

import traceback
import pycurl
import cStringIO
from sys import exc_info

c = pycurl.Curl();

def _initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    c.setopt(c.CONNECTTIMEOUT_MS, 150)
    c.setopt(c.TIMEOUT_MS, 150)
    c.setopt(pycurl.NOSIGNAL, 1)
#    client_socket.connect((HOST,int(PORT)))
#    print "client_socket after connect : --"+ str(client_socket) +"--"

def _process(HOST, PORT, GET,client_socketport=None):
    data = cStringIO.StringIO()
    uri = "http://"+HOST+":"+str(PORT)+GET;
    c.setopt(c.URL, uri);
    c.setopt(c.WRITEFUNCTION, data.write)
    try:
        c.perform();
        response = data.getvalue();
    except:
        print("Did not get response ",exc_info(), uri, traceback.format_exc())
        response = (GET.split("time=")[1]).split("&")[0]
    return response

def processCTRL(HOST, PORT, GET,HOST2):
    try:
        #https://dweet.io/get/latest/dweet/for/my-thing-name
        #get the control value
        response=""
        response = json.loads(_process("dweet.io",80,"/get/latest/dweet/for/%s"%(HOST.strip("&]"))));
        
        #https://dweet.io/dweet/for/my-thing-name?hello=world
        request = (response['with'][0]['content'][PORT]).replace("X","&")
        #actually use the request, and then get the current state
        state = interpret(request);
        if request.find("init")>=0:
            state = interpret("/state");
        
        #send the state value
        _process("dweet.io",80,"/dweet/for/%s?%s='%s'"%(HOST2,'state',state.replace("&","X")));
    
    except Exception, err:
        print("[Warning] in dweet client send and receive :%s\n " % err, response)



if __name__ == "__main__":
    signal.signal(signal.SIGALRM, updateState)
    signal.setitimer(signal.ITIMER_REAL, h, h)
    
    rate = .1
    
    control_action = 'control_action' #get value as a string from arguments
    port = 'ctrl' #get value as a string from arguments
    plant_state = 'plant_state' #get value as a string from arguments
    
    try:
        '''
            # Simply keeps python from exiting until this node is stopped
            for dweet in dweepy.listen_for_dweets_from(control_action):
            print dweet
            callback(dweet['content'][port]);
            '''
        while 1:
            _newt0=clock();
            processCTRL(control_action, port, "ctrl", plant_state);
            while(clock()< _newt0+rate): pass; #sleep for a specified amount of time.


except (KeyboardInterrupt, SystemExit):
    print exc_info()
        print "Shutting down service"