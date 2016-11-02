from re import search
import urllib2
from sys import exc_info

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
        pass;

# Method to read URL
def process(HOST, PORT, GET, client = None):
        try:
            data = urllib2.urlopen("http://"+HOST+":"+str(PORT)+GET, None, timeout=.150);
            response = data.read();
            data.close()

            m = search('\[(.+?)\]', response);
            if m:
                response = m.groups()[-1];
                data = response.split()
        except:
                print("Did not get response: ",exc_info());
                response = (GET.split("time=")[1]).split("&")[0]
        return response

if __name__ == "__main__":
    host = '130.127.192.68' 
    data = '/state'
    port = 9163
    print process(host, port, data);


