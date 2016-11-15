from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node, Host, RemoteController
from mininet.log import setLogLevel, info
from mininet.util import quietRun, dumpNodeConnections
from mininet.cli import CLI
from mininet.node import OVSController, Controller
from mininet.link import TCLink

#/etc/init.d/openvswitch-switch start

import time
class myTopo(Topo):
    def __init__(self, **ops):
        super(myTopo, self).__init__(**ops)
        servers = [['broker', self.addHost('h1')], ['controller', self.addHost('h2')], ['plant', self.addHost('h3')]]

        switches = []
        for i in range(3):
            switches.append(self.addSwitch('s' + str(i + 1)))

        #linking servers to respective switches... I may not need to use switches
        for i in range(3):
            self.addLink(servers[i][1], switches[i])#, delay='1000ms')


        #linking all switches to broker switch
        for i in range(1, 3):
            self.addLink(switches[0], switches[i])



def myNet(net, sampleInterval = '.1', directory = 'ballplate/'):
    h1, h2, h3 = net.getNodeByName('h1', 'h2', 'h3')


    import subprocess
    i = 1;
    t = "trial" + str(i)
    import pexpect
    while t in pexpect.run("ls"):
        i += 1;
        t = "trial" + str(i);
    subprocess.call(['mkdir',t])
    #start tcp dump on all servers in a file with the time
    servers = [['Broker', h1],['Plant', h2],['Controller', h3]]
    for i in range(0, len(servers)):
        servers[i][1].cmd('tcpdump -w ' + t + '/' + servers[i][0] +  '.pcap &')
    from datetime import datetime
    dt = datetime.now()
    subprocess.call(["echo", '"' + dt.strftime('%b-%d-%H:%M.%S') +'"', ">", t +"/time.txt"])


    brokerLoc = "10.0.0.1"
    h1.cmd("ifconfig > "+t+"/h1.txt")

    brokersRunning = 'mosquitto -p 9883 > ' + 'mosquittoOutput.txt &'
    plantsRunning = 'python nlmodel_mqtt.py ' + brokerLoc + ' 9883 uisgroup/control_action__1__uisgroup/plant_state__1 &' 
    controllersRunning = 'cd '+ t + '; python ../nlcontroller.py mqtt bar ' + brokerLoc + ' 9883 n2oEast_new 20 ' + sampleInterval + ' 6.09 3.5 -5.18 -12.08 6.58 -0.4 > controllerOut.txt &'

    h1.sendCmd(brokersRunning)
    h2.sendCmd(plantsRunning)
    h3.sendCmd(controllersRunning)
    time.sleep(21)
    

def run():

    net = Mininet(topo = myTopo(), link = TCLink)
    net.start()
    myNet(net)
    #CLI(net)
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


        
