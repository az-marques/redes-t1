# A router should run this ...

from scapy.all import *
import NetInterface

def example(pkt):
	pkt.show()
	if pkt.sniffed_on == 'r-eth1' and pkt[IP].dst == '10.2.2.1':
		pkt[Ether].dst = None
		sendp(pkt, iface='r-eth2')
	elif pkt.sniffed_on == 'r-eth2' and pkt[IP].dst == '10.1.1.1':
		pkt[Ether].dst = None
		sendp(pkt, iface='r-eth1')
	else:
		return

      # iface defined in NetInterface
sniff(iface=NetInterface.getIface(), filter='ip',  prn=example)