#version 1:
from re import search
import socket
import sys


# client_socket_socket = None
socket.SOCK_DCCP                = 6
socket.IPPROTO_DCCP             = 33

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DCCP, socket.IPPROTO_DCCP)
    client_socket.settimeout(.150)

#     print "client connected"
except socket.error, (code,message):
    if client_socket:
        client_socket.close()
    print "Could not open socket: " + message
    sys.exit(1)

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
    client_socket.connect((HOST,int(PORT)))
#    print "client_socket after connect : --"+ str(client_socket) +"--"

def process(HOST, PORT, GET,client_socketport=None):
    try:
#         client_socket.send(GET+"&]")
        client_socket.sendall(GET+"&]")      #This is for test to see that it actually send whole message at once or not
#         print "send : "+GET
        response = client_socket.recv(1024) # buffer size is 1024 bytes
#         print "response : "+response
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
    except socket.error, msg:
        sys.stderr.write("[ERROR] in DCCP client send and receive :%s\n " % msg)
        response = (GET.split("time=")[1]).split("&")[0]
    return response

if __name__ == "__main__":
    print process(host, port, data);

