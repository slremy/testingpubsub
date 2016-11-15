from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node, Host, RemoteController
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.util import quietRun, dumpNodeConnections
from mininet.cli import CLI
from mininet.node import OVSController, Controller
import subprocess

#/etc/init.d/openvswitch-switch start
#link latency 2, 40, 200 ms  -ping from host 1 to host 2
#interval
#1 hour for each run
#application layer in skype chat 
import time
DELAY = '20ms'
class myTopo(Topo):
    def init(self, DELAY='20ms', **ops):
        print(DELAY)

        #super(myTopo, self).__init__(**ops)
        servers = [['broker', self.addHost('h1')], ['controller', self.addHost('h2')], ['plant', self.addHost('h3')]]

        switches = []
        for i in range(3):
            switches.append(self.addSwitch('s' + str(i + 1)))

        #linking servers to respective switches... I may not need to use switches
        for i in range(3):
            self.addLink(servers[i][1], switches[i])


        #linking all switches to broker switch
        for i in range(1, 3):
            self.addLink(switches[0], switches[i])




def myNet(net, commands = {}, t = ""):
    h1, h2, h3 = net.getNodeByName('h1', 'h2', 'h3')

    #start tcp dump on all servers in a file with the time
    servers = [['Broker', h1],['Plant', h2],['Controller', h3]]
    for i in range(0, len(servers)):
        servers[i][1].cmd('tcpdump -w ' + t + '/' + servers[i][0] +  '.pcap &')
    from datetime import datetime
    dt = datetime.now()
    subprocess.call(["echo", '"' + dt.strftime('%b-%d-%H:%M.%S') +'"', ">", t +"/time.txt"])
    
    h1.sendCmd(commands['broker'])
    h2.sendCmd(commands['plant'])
    h3.cmd(commands['controller'])
    

def run():
    version = raw_input("kafka(k)  or MQTT(m): ")
    commands = {}
    t = setTrial()
    if 'm' in version: commands = updateMQTTCommands(t)
    else: commands = updateKafkaCommands(t)
    
    mine = myTopo(DELAY='5ms')
    net = Mininet(topo = mine, controller = OVSController)
    net.start()
    myNet(net, commands, t)
    CLI(net)
    net.stop()


brokerLoc = "10.0.0.1"
ballplate = '../myBallPlate/'
sampleInterval = '.1'
def setTrial():
    i = 1;
    t = "trial" + str(i)
    import pexpect
    while t in pexpect.run("ls"):
        i += 1;
        t = "trial" + str(i);
    subprocess.call(['mkdir',t])
    return t

def updateMQTTCommands(t):
    commands = {}
    commands['broker'] = 'mosquitto -p 9883 > ' + t + '/mosquittoOutput.txt &'
    commands['plant'] = 'python ' + ballplate + 'nlmodel_mqtt.py ' + brokerLoc + ' 9883 ' + t+'/uisgroup_control_action__1__uisgroup_plant_state__1 &'
    commands['controller'] = 'python ' + ballplate + 'nlcontroller.py mqtt bar ' + brokerLoc +' 9883 ' + t + '/n2oEast_kodiaodsfijng_new 20 ' + sampleInterval + ' 6.09 3.5 -5.18 -12.08 6.58 -0.4 > ' + t +'/controllerOut.txt'
    return commands

def updateKafkaCommands(t):
    commands = {}
    commands['broker'] = 'mosquitto -p 9883 > ' + 'mosquittoOutput.txt &'
    commands['plant'] = 'python ' + ballplate + 'nlmodel_mqtt.py ' + brokerLoc + ' 9883 uisgroup_control_action__1__uisgroup_plant_state__1 &'
    commands['controller'] = 'python ' + ballplate + 'nlcontroller.py mqtt bar ' + brokerLoc + ' 9883 n2oEast_kodiaodsfijng_new 20 ' + sampleInterval + ' 6.09 3.5 -5.18 -12.08 6.58 -0.4 > ' + t +'/controllerOut.txt'
    return commands


    
if __name__ == '__main__':
    run()


        
