from scapy.all import *
from scapy.all import *
import threading
import time

import BabelSpeaker
import NetInterface


class BabelHello(Packet):
    name = "BabelHello"
    fields_desc = [
        ByteField("type", 0x01), # TLV type for Hello
        ShortField("seqno", 0), # Sequence number
        ShortField("interval", 0) # Interval for Hello
    ]

class BabelIHeardU(Packet):
    name = "BabelIHU"
    fields_desc = [
        ByteField("type", 0x02), # TLV type for IHU
        ShortField("seqno", 0), # Sequence number
        ShortField("interval", 0) # Interval for Hello
    ]

class BabelPacket(Packet):
    name = "BabelPacket"
    fields_desc = [
        ByteField("magic", 42), # Babel magic number
        ByteField("version", 1), # Babel version
        ShortField("length", 0) # Payload length
    ]

class Node:
    def __init__(self, babel_speaker, iface):
        self.babel_speaker = babel_speaker # Speaker as defined in BabelSpeaker.py
        self.iface = iface # Network interface

    def send_hello(self, destination, seqno, interval):
        hello_tlv = BabelHello(seqno=seqno, interval=interval)

        # Create a packet and say Hello :D
        babel_pkt = BabelPacket() / hello_tlv
        babel_pkt.length = len(babel_pkt) - 4  # excluding header

        # Send packet to the destination address
        sendp(Ether()/IP(dst=destination)/babel_pkt, iface=self.iface, verbose=False)

    def send_ihu(self, destination, seqno, interval):
        # Create IHU TLV acknowledging Hello
        iheardyou_tlv = BabelIHeardU(seqno=seqno, interval=interval)

        # Create a packet and add the IHU TLV to it
        babel_pkt = BabelPacket() / iheardyou_tlv
        babel_pkt.length = len(babel_pkt) - 4  # Length excluding header

        # Send the packet to the destination address using the Babel protocol
        sendp(Ether()/IP(dst=destination)/babel_pkt, iface=self.iface, verbose=False)

    def forward_packet(self, packet):
        if IP in packet:
            destination_ip = packet[IP].dst
            next_hop = self.babel_speaker.find_route(destination_ip)

            if next_hop:
                sendp(packet, iface=self.iface, verbose=False)
            else:
                print(f"No route found for {destination_ip}")

    def handle_incoming_packet(self, packet):
        # Parse Babel packets
        if BabelPacket in packet:
            # Check if it's a BabelHello
            if packet.haslayer(BabelHello):
                hello = packet[BabelHello]
                print(f"Received Hello from {packet[IP].src}")
                self.babel_speaker.receive_tlv_hello(hello)
                # Send an IHU response for the Hello message
                self.send_ihu(packet[IP].src, hello.seqno, hello.interval)

            # Check if it's a BabelIHeardYou
            elif packet.haslayer(BabelIHeardU):
                ihu = packet[BabelIHeardU]
                self.babel_speaker.receive_tlv_hello(ihu)
                print(f"Received IHeardYou from {packet[IP].src}")

            else:
                print("Babel packet received with an unknown TLV type.")
        else:
            print("Non-Babel packet received.")

    def start_sniffing(self):
        sniff(iface=self.iface, prn=self.handle_incoming_packet, filter="ip", store=0)


def init_node():
    babel_speaker = BabelHello.BabelSpeaker()  # BabelSpeaker instance
    node = Node(babel_speaker, iface=NetInterface.getIface())  # JustMininetThings

    # Start sniffing in a separate thread
    threading.Thread(target=node.start_sniffing, daemon=True).start()

    # Periodically send Hello messages
    seqno = 0
    while True:
        destination = "someAddress"  # Find way to get address i guess??
        interval = 1000              # 1 second interval
        node.send_hello(destination, seqno, interval)
        seqno += 1                   # Increment sequence number
        time.sleep(interval / 1000) 

# Run
if __name__ == "__main__":
    pass
