import httplib
from sys import exc_info

connection=None;

def initialize_handshake(HOST, PORT):    # setup socket and start the connection to the model
        global connection;
        connection=httplib.HTTPConnection(HOST+":"+str(PORT), timeout=.150);

# Method to read URL
def process(HOST, PORT, GET, client = None):
        global connection;
        try:
		connection.request('GET', GET+"&]");
		data = connection.getresponse();
		if data.status == 200: 
			response = data.read();
		else: 
			print "bad status"
			response = "0";
        except:
                print("Did not get response: ",exc_info());
                response = (GET.split("time=")[1]).split("&")[0]
        return response

if __name__ == "__main__":
    host = '130.127.192.68' 
    data = '/state'
    port = 9163
    print process(host, port, data);

