from nlmodel import *
import threading
import socket
notFinished = True 
buffer_size = 1024	#the buffer size for listening socket (Bytes)
backlog = 5		#used in listen method (TCP and DCCP)

if __name__ == "__main__":
 
    #create the UDP socket server (create the socket, and then listen until you can't)
    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error, (code,message):
        if server:
            server.close()
        print "Could not open socket: " + message
        exit(1)
 
    server.bind(("", port))
    print("%s:%d" % ("0.0.0.0", port))
 
    # Communications sub Thread class & function  $$
    class myserver_thread (threading.Thread):
        def __init__(self, threadID, name):
            threading.Thread.__init__(self)
        def run(self):
            while True:
                sleep(.0001);
                try:
                    data, addr = server.recvfrom(buffer_size) 
                    server.sendto(interpret(data), addr) #send response back
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
            server_thread.join()
            #server.close()
            signal.setitimer(signal.ITIMER_REAL, 0, h)
            print(exc_info())
            print("Shutting down service")
