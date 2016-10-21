from mininet.topo import Topo

class MyTopology(Topo):
    def __init__(self):
        Topo.__init__(self)
        controller = self.addHost('h1')
        broker = self.addHost('h2')
        plant = self.addHost('h3')
        cSwitch = self.addSwitch('s1')
        bSwitch = self.addSwitch('s2')
        pSwitch = self.addSwitch('s3')

        self.addLink(controller, cSwitch)
        self.addLink(cSwitch, bSwitch)


        self.addLink(plant, pSwitch)
        self.addLink(pSwitch, bSwitch)

        self.addLink(bSwitch, broker)


topos = {'myTopology' : ( lambda: MyTopology() ) }

import time
time = time.time()
h1.cmd('tcpdump -w h1' + str(time) + '.pcap &');
h2.cmd('tcpdump -w h2' + str(time) + '.pcap &');
h3.cmd('tcpdump -w h3' + str(time) + '.pcap &');
