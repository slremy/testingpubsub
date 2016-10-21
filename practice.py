from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node, Host, RemoteController
from mininet.log import setLogLevel, info
from mininet.util import quietRun, dumpNodeConnections

import time
class myTopo(Topo):
    def __init__(self, **ops):
        super(myTopo, self).__init__(**ops)
        servers = [['broker', self.addHost('h1')], ['controller', self.addHost('h2')], ['plant', self.addHost('h3')]]
        switches = []
        for i in range(3):
            switches.append(self.addSwitch('s' + str(i + 1), dpid=("000000000000000" + str(i + 1))))

        #linking servers to respective switches... I may not need to use switches
        for i in range(3):
            self.addLink(servers[i][1], switches[i]) 
        
        #linking together all switches to the brokers switch
        for i in range(1, len(switches)):
            self.addLink(switches[i], switches[0])


    #sample interval = latency
def myNet(net, sampleInterval = '.1', directory = 'ballplate/'):
    #servers = [['h1', Host('h1')], ['h2', Host('h2')], ['h3', Host('h3')]]

    h1, h2, h3 = net.getNodeByName('h1', 'h2', 'h3')

    #from datetime import datetime
    #dt = datetime.now()
    #t = dt.strftime('%b-%d-%H:%M.%S')
    #import subprocess
    #subprocess.call(['mkdir',t])
    #start tcp dump on all servers in a file with the time
#    for i in range(0, len(servers)):
#        servers[i][1].cmd('tcpdump -w ' + t + '/' + servers[i][0] +  '.pcap &')


    brokerLoc = '10.0.0.1'
    #    servers[0][1].cmd("ifconfig > s1.txt")
    h1.cmd("ifconfig > h1.txt")

    brokersRunning = 'mosquitto -p 9883 > ' + 'mosquittoOutput.txt '
    plantsRunning = 'python nlmodel_mqtt.py ' + brokerLoc + ' 9883 uisgroup/control_action__1__1uisgroup/plant_state__1' 
    controllersRunning = 'python nlcontroller.py mqtt bar ' + brokerLoc + ' 9883 n2oEast_kodiaodsfijng_new 20 ' + sampleInterval + ' 6.09 3.5 -5.18 -12.08 6.58 -0.4 > controllerOut.txt'

    print("done, " + controllersRunning)

    #servers[0][1].sendCmd(brokersRunning)
    #servers[1][1].sendCmd(plantsRunning)
    #servers[2][1].sendCmd(controllersRunning)
    h1.sendCmd(brokersRunning)
    h2.sendCmd(plantsRunning)
    h3.cmd(controllersRunning)


def run():
    #c = RemoteController('c', '0.0.0.0', 6633)
    net = Mininet(topo=myTopo(), controller=None)
    #net.addController(c)
    net.start()
    myNet(net)
    net.stop()
    #net.start()
    #info( "Dumping host connections\n" )
    #dumpNodeConnections(net.hosts)
    #info( "Testing bandwidth between h1 and h4\n" )
    #h1, h2 = net.getNodeByName('h1', 'h2')
    #net.iperf( ( h1, h2 ), l4Type='UDP' )
    #net.stop()
if __name__ == '__main__':
    #for latency in [0, .005, .02]:
    run()


        
