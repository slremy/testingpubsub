from re import search
import socket
import sys

# setup socket
client = None
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(.150)
except socket.error, (code,message):
    print "Could not open socket: " + message
    sys.exit(1)

# Method to read URL
def process(HOST, PORT, GET, clientport = None):
  #print GET, (HOST, int(PORT))

  try:
        client.sendto(GET, (HOST, int(PORT)))
        response, addr = client.recvfrom(1024) # buffer size is 1024 bytes
        m = search('\[(.+?)\]', response);
        if m:
            response = m.groups()[-1];
        data = response.split()
  except socket.error, msg:
        sys.stderr.write("[ERROR] in udp client send and receive :%s\n " % msg)
        response = (GET.split("time=")[1]).split("&")[0]

  return response

if __name__ == "__main__":
    host = '130.127.192.68' 
    data = '/state'
    port = 9163
    print process(host, port, data);

