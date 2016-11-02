#version 2:
from re import search
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
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
    except:
        print("Did not get response ",exc_info(), uri, traceback.format_exc())
        response = (GET.split("time=")[1]).split("&")[0]
    return response

plant_state = 'plant_state'

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    _initialize_handshake(HOST, PORT);#  could check that the things are actually there



def process(HOST, PORT, GET,client_socketport=None):
    #https://dweet.io/dweet/for/my-thing-name?hello=world
    #send the control value
    _process("dweet.io",80,"/dweet/for/%s?%s='%s'"%(HOST,PORT,GET.replace("&","X")));
    #https://dweet.io/get/latest/dweet/for/my-thing-name
    #get the plant_state
    try:
        dweet = json.loads(_process("dweet.io",80,"/get/latest/dweet/for/%s"%(plant_state)))
        response = dweet['with'][0]['content']['state'].replace("X","&").strip("'");
    #response = _process("dweet.io",80,"/get/latest/dweet/for/%s"%(plant_state))[0]['content']['state'].replace("X","&");
    except Exception, err:
        print("[Warning] in dweet client send and receive :%s\n " % err, "/get/latest/dweet/for/%s"%(plant_state))
        response = (GET.split("time=")[1]).split("&")[0]
    return response;

if __name__ == "__main__":
    initialize_handshake(None, None);
    print process(None, None, "/init");
