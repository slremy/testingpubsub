#version 1:
import socket
import sys


# client_socket_socket = None
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
#         client_socket.send("GET %s HTTP/1.0\r\nHost: %s\r\n\r\n" % (GET+"&]", HOST))
        client_socket.sendall("GET %s HTTP/1.1\r\nHost: %s\r\n\r\n" % (GET, HOST))      #This is for test to see that it actually send whole message at once or not
#         print "send : "+GET
        response = client_socket.recv(1024) # buffer size is 1024 bytes
        data = response.split("\r\n")
        response = data[len(data) - 4].split("]")[0];
        print response
    except socket.error, msg:
        sys.stderr.write("[ERROR] in TCP client send and receive :%s\n " % msg)
        response = ""
    return response

if __name__ == "__main__":
    print process(host, port, data);

