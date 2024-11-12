# copiado do professor na cara dura

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.host import Host
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class BasicTopo(Topo):
    "A LinuxRouter connecting two hosts"

    def build(self, **_opts):
        router = self.addHost('r', ip=None)
        host1 = self.addHost('h1', ip=None, defaultRoute='via 10.1.1.254')
        host2 = self.addHost('h2', ip=None, defaultRoute='via 10.2.2.254')
        self.addLink(host1, router, 
             intfName1='h1-eth0', params1={'ip':'10.1.1.1/24'},
             intfName2='r-eth1', params2={'ip':'10.1.1.254/24'})
        self.addLink(host2, router, 
             intfName1='h2-eth0', params1={'ip':'10.2.2.1/24'},
             intfName2='r-eth2', params2={'ip':'10.2.2.254/24'})
        

def getIface():
    return ["r-eth1","r-eth2"]


# This takes a path and executes it 
def run_router_program(host, path):
    host.cmd(f'python3 {path} &')

def run():
    net = Mininet(topo=BasicTopo(), controller=None)
    for _, v in net.nameToNode.items():
     for itf in v.intfList():
      v.cmd('ethtool -K '+itf.name+' tx off rx off')
    
    net.start()

    # Path to the Node program script
    babel_router_program_path = './Node.py'
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    # Runs the Node.py program on each host
    run_router_program(h1, babel_router_program_path)
    run_router_program(h2, babel_router_program_path)

    # command line interface!
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()