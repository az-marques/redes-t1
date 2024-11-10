from BabelSpeaker import BabelSpeaker
from Interface import Interface
from RepeatedTimer import RepeatedTimer
from BitVector import BitVector

class Neighbour():
    def __init__(self, speaker: BabelSpeaker, interface: Interface, address, mcast_ne, ucast_ne, mcast_interval, ucast_interval, ihu_interval) -> None:
        #the Babel speaker/node to whom this neighbour belongs to (used for flush)
        self.speaker = speaker
        #The local node's interface over which this neighbour is reachable
        self.interface = interface
        #The address of the neighbouring interface
        self.address = address
        #A history of recently received Multicast Hello packets from this neighbour.
        self.mcast_hello_hist = BitVector(size=16)
        #A history of recently received Unicast Hello packets from this neighbour.
        self.ucast_hello_hist = BitVector(size=16)
        #The "transmission cost" value from the last IHU packet received from this neighbour, or (infinity) if the IHU hold timer for this neighbour has expired;
        self.txcost = float('inf') #no clue what to initialize this as
        #The expected incoming Multicast Hello sequence number for this neighbour.
        self.mcast_ne = mcast_ne
        #The expected incoming Unicast Hello sequence number for this neighbour.
        self.ucast_ne = ucast_ne
        #The outgoing Unicast Hello sequence number for this neighbour.
        self.ucast_hello_seqno = 0 #is 0 okay?????
        
        self.mcast_timer = RepeatedTimer(mcast_interval, self._history_timeout, [self, True])
        if mcast_interval != None: #maybe we can have them always not started by default?
            self.mcast_timer.start()
        
        self.ucast_timer = RepeatedTimer(ucast_interval, self._history_timeout, [self, False])
        if ucast_interval != None:
            self.ucast_timer.start()
        
        self.ihu_timer =  RepeatedTimer(ihu_interval, self._ihu_timeout, [self])
        if ihu_interval != None:
            self.ihu_timer.start()

    def index(self):
        return self.interface, self.address
    
    def cost(self):
        #implementing k-out-of-j for now, probably replace with ETX later
        #k = 16 (vector lenght, don't need to do anything for this)
        j = 8
        if self.mcast_hello_hist.count_bits() >= 8 or self.ucast_hello_hist.count_bits() >= 8:
            #If either of the instances of k-out-of-j indicates that the link is up, then the link is assumed to be up, and the rxcost is set to... not infinty
            return self.txcost
        else:
            return float('inf') #work out a consistent definition of infinity later
        
    def receive_ihu_from(self, rxcost, interval):
        self.txcost =  rxcost

        self.ihu_timer.stop()
        self.ihu_timer.interval = interval*1.5
        self.ihu_timer.start()

    def _ihu_timeout(self):
        self.txcost = float('inf') #work out a consistent definition of infinity later
    
    def receive_hello_from(self, is_multicast, seqno, interval):
        if is_multicast:
            history = self.mcast_hello_hist
            ne = self.mcast_ne
            timer =  self.mcast_timer
        else:
            history = self.ucast_hello_hist
            ne = self.ucast_ne
            timer =  self.ucast_timer

        #don't have the modulo stuff in cause that depends on how we even implement seqnos and that's a whole mess
        #if the two differ by more than 16 (modulo 2^16), then the sending node has probably rebooted and lost its sequence number; the whole associated neighbour table entry is flushed and a new one is created
        if abs(ne - seqno) > 16:
            self.flush(True) #but we have to make it re-add itself somehow
            return
        #otherwise, if the received seqno nr is smaller (modulo 2^16) than the expected sequence number ne, then the sending node has increased its Hello interval without our noticing; the receiving node removes the last (ne - nr) entries from this neighbour's Hello history (we "undo history");
        elif seqno < ne:
            history.shift_right(ne-seqno)
        #otherwise, if nr is larger (modulo 2^16) than ne, then the sending node has decreased its Hello interval, and some Hellos were lost; the receiving node adds (nr - ne) 0 bits to the Hello history (we "fast-forward").
        elif seqno > ne:
            history.shift_left(seqno-ne)
        
        #add 1 to the end of history (hello received)
        history.shift_left(1)
        history[-1]=1

        #set expected seqno to received seqno+1
        if is_multicast:
            self.mcast_ne = seqno + 1
        else:
            self.ucast_ne = seqno + 1

        #If the Interval field of the received Hello is not zero, it resets the neighbour's hello timer to 1.5 times the advertised Interval (the extra margin allows for delay due to jitter).
        if interval != 0:
            timer.stop()
            timer.interval = interval*1.5
            timer.start()
    
    def _history_timeout(self, is_multicast):
        if is_multicast:
            self.mcast_hello_hist.shift_left(1)
            self.mcast_ne += 1
        else:
            self.ucast_hello_hist.shift_left(1)
            self.ucast_ne +=1

        if self.mcast_hello_hist == BitVector(size=16) and self.ucast_hello_hist == BitVector(size=16):
            self.flush(False)
            return
        #not empty, keep the timer going

    def flush(self, readd: bool):
        self.speaker.flush_neighbour(self)
