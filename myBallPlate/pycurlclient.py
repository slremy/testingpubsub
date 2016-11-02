#version 1:
from re import search
import traceback
import pycurl
import cStringIO
from sys import exc_info

c = pycurl.Curl();

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    c.setopt(c.CONNECTTIMEOUT_MS, 150)
    c.setopt(c.TIMEOUT_MS, 150)
    c.setopt(pycurl.NOSIGNAL, 1)
#    client_socket.connect((HOST,int(PORT)))
#    print "client_socket after connect : --"+ str(client_socket) +"--"
            
def process(HOST, PORT, GET,client_socketport=None):
    data = cStringIO.StringIO()
    uri = "http://"+HOST+":"+str(PORT)+GET+"&]"
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
        #print("Did not get response ",exc_info(), uri, traceback.format_exc())
        response = (GET.split("time=")[1]).split("&")[0]
    return response

if __name__ == "__main__":
    print process(host, port, data);

