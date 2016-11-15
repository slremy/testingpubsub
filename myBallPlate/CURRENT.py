from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from sys import argv


import time, pexpect

class myTopo(Topo):
    def build(self, Lpct = 0, D = '5ms', wait = 5, **opts):

        switches = []
        hosts = []
        k = 3

        #generating switches and hosts and then connecting them respectively
        for i in range(k):
            switches.append(self.addSwitch('s%s' % (i + 1)))
            hosts.append(self.addHost('h%s' % (i + 1), cpu=.5 / k))
            self.addLink(hosts[i], switches[i], bw=10, use_htb=True)

        
        #finishing network topology
        self.addLink(switches[0], switches[1], bw=10, delay=D, loss= Lpct, use_htb=True)
        self.addLink(switches[0], switches[2], bw=10, delay=D, loss= Lpct, use_htb=True)




def setTrial(i = 1, addition = 'mqtt'):
    t = addition + '_trial'
    while (t + str(i)) in pexpect.run('ls'): i += 1

    pexpect.run('mkdir ' + t + str(i))
    return [t + str(i), i]

def toArg(commands = ['ls','ls']):
    res = '"'
    for s in commands:
        res += s + ' "   "'

    res += '"'
    return res
                
def mqttRun():

    dty = setTrial(1, 'mqtt')[0]
    runTime = '20'
    interval = '.1'

    cmds = []
    brokerCommands = ['tcpdump -w broker.pcap', '{ mosquitto -p 9883 } 2> mosquittoStdout.txt']
    plantCommands = ['tcpdump -w plant.pcap', '{ python ../nlmodel_mqtt.py 10.0.0.1 9883 } 2> plantStdout.txt']
    ctrlCommands = ['tcpdump -w controller.pcap', '{ python ../nlcontroller.py mqtt bar 10.0.0.1 9883 controlOutput 20 .1  6.09 3.5 -5.18 -12.08 6.58 -0.4 } 2> controllerStdout.txt' ]

    #will the broker always be there?
    
    
        
                
    lossPct = 0
    delay = '10ms'
    waitTime = 22
    
    topo = myTopo(Lpct = lossPct, D = delay, wait = waitTime)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, autoStaticArp=True )


    net.start()
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    

    #Logging commands
    fout = open(dty + '/commands.txt', 'w')
    fout.write('Loss Percent: ' + str(lossPct) + '\n')
    fout.write('Delay: ' + str(delay) + '\n')
    fout.write('Wait time: ' + str(waitTime) + '\n\n')
    fout.close()
        
    from datetime import datetime
    start = datetime.now()



    for i in range(3): net.getNodeByName('h%s' % (i + 1)).cmd('cd ' + dty)
    #sending out all the commands

    net.getNodeByName('h1').cmd('python ../runCommands.py ' + str(waitTime + 2) + '  ' + toArg(brokerCommands) + ' &')
    net.getNodeByName('h2').cmd('python ../runCommands.py ' + str(waitTime + 1) + '  ' + toArg(plantCommands) + ' &')
    net.getNodeByName('h3').cmd('python ../runCommands.py ' + str(waitTime)     + '  ' + toArg(ctrlCommands) + ' &')

    time.sleep(waitTime  + 3)
#    net.getNodeByName('h1').sendCmd('mosquitto -p 9888 > mosquittoOutput.txt')
#    net.getNodeByName('h1').sendCmd('ifconfig > ifcfig.txt')
#    net.getNodeByName('h2').sendCmd(cmds[1])
#    net.getNodeByName('h3').sendCmd(cmds[2])

#    

    end = datetime.now()
    fout = open(dty + '/time.txt', 'w')
    fout.write('Start: '  + start.strftime('%b-%d-%H:%M.%S') + '\n')
    fout.write('End: ' + end.strftime('%b-%d-%H:%M.%S') + '\n')


    
    
    #CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel( 'info' )
    mqttRun()
