from nlmodel import *
import threading
import socket
from re import search
notFinished = True
buffer_size = 1024	#the buffer size for listening socket (Bytes)
backlog = 5		#used in listen method (TCP and DCCP)
 
if __name__ == "__main__":
 
    #create the TCP socket server (create the socket, and then listen until you can't)
    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	#TCP
    except socket.error, (code,message):
        if server:
            server.close()
        print "Could not open socket: " + message
        exit(1)
 
    server.bind(("", port))
    server.listen(backlog)		# only TCP and DCCP need this 
    print("%s:%d" % ("0.0.0.0", port))
 
    # Communications sub Thread class & function  $$
    class myserver_thread (threading.Thread):
        def __init__(self, threadID, name):
            threading.Thread.__init__(self)

        def run(self):
            while (notFinished):
                data = ""
                server_session, addr = server.accept()    #start a session to a controller
                print "New connection from ", addr    
                sleep(.0001);
                while (notFinished):
                    try:
                        data += server_session.recv(buffer_size)
                        #print ("Recv TCP:'%s'" % data)
                        m = search('(.+?)]', data)
                        if m:
                            server_session.send(interpret(m.group(1))) #send response back
                            data = ""
                    except: 
                        print "nothing good", exc_info()

    server_thread = myserver_thread(1, "server_thread")
    server_thread.daemon = True
    server_thread.start()
 
    signal.signal(signal.SIGALRM, updateState)
    signal.setitimer(signal.ITIMER_REAL, h, h)
 
 
    #wait until you can't listen anymore
    while notFinished:
        try:
            pass;
        except (KeyboardInterrupt, SystemExit):
            notFinished = False
            server_thread.join()
            #server.close()
            signal.setitimer(signal.ITIMER_REAL, 0, h)
            print(exc_info())
            print("Shutting down service")

