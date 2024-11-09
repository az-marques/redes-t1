from BitVector import BitVector
from RepeatedTimer import RepeatedTimer

class _Interface():
    def __init__(self, id) -> None:
        self.id = id
        self.multicast_hello_seqno = 0
    def __str__(self) -> str:
        return str(self.id)

class _Neighbour():
    def __init__(self, speaker, interface: _Interface, address, mcast_ne, ucast_ne, mcast_interval, ucast_interval, ihu_interval) -> None:
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
            self.flush()
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
            self.flush()
            return
        #not empty, keep the timer going

    def flush(self):
        self.speaker.flush_neighbour(self)
        

class _Source():
    def __init__(self, prefix, router_id) -> None:
        self.prefix = prefix
        self.router_id = router_id
        self.f_seqno
        self.f_metric
        #add source garbage collection timer at some point
    def index(self):
        return self.prefix, self.router_id
    def compare_index(self, prefix, router_id) -> bool:
        return prefix == self.prefix and router_id == self.router_id
        
class _Route():
    def __init__(self, source: _Source, neighbour: _Neighbour, metric, seqno, next_hop, selected) -> None:
        self.source = source
        self.neighbour = neighbour
        self.metric = metric
        self.seqno = seqno
        self.next_hop = next_hop
        self.selected = selected
    def index(self):
        return self.source.prefix, self.neighbour

    def compare_index(self, prefix, neighbour) -> bool:
        return prefix == self.source.prefix and neighbour == self.neighbour

    
class BabelSpeaker ():
    #node_seqno
    #pending_seqno_table
    inf = float('inf') #defining this here cause we might want to change it later
    def __init__(self) -> None:
        #router id??
        self.seqno = 0
        self.interfaces = []
        self.neighbours = []
        self.sources = []
        self.routes = []
    
    def update(self, prefix, neighbour: _Neighbour, router_id, seqno, advertised_metric):
        next_hop = neighbour.address #VERY PROBABLY WRONG CHANGE THIS LATER
        metric = self._compute_metric(neighbour, next_hop)
        r = self._has_route(prefix, neighbour)
        source = self._has_source(prefix, router_id) #this whole section feels wrong and I don't know why
        update_feasible = self._is_feasible(source, seqno, metric)

        #change later to make it store unfeasible routes somewhere separate for seqno requests?
        if r == None:
            if (not update_feasible) or metric >= self.inf:
                #ignore
                pass
            else:
                if source == None:
                    #add the fucking source somehow idk
                    pass
                self._add_route(source, neighbour, seqno, metric, neighbour.address)
                pass  
        else: 
            if r.selected and (not update_feasible) and (router_id == r.source.router_id):
                #ignore
                pass
            else:
                self._add_route(r.source, neighbour, seqno, metric, next_hop)


    def _compute_metric(self, neighbour, advertised_metric):
        #PLACEHOLDER
        return advertised_metric+neighbour.tcost
    
    def _is_feasible(self, source, seqno, metric):
        return source == None or metric >= self.inf or source.f_seqno<seqno or (source.f_seqno==seqno and metric<source.f_metric)

    def _has_route(self, prefix, neighbour) -> _Route:
        for r in self.routes:
            if _Route(r).compare_index(prefix, neighbour):
                return r
        return None
    
    def _has_source(self, prefix, router_id):
        for s in self.sources:
            if _Source(s).compare_index(prefix, router_id):
                return s
        return None
  
    def _add_route(self, source: _Source, neighbour: _Neighbour, seqno, metric, next_hop):
        r = _Route(source, neighbour, metric, seqno, next_hop, False)
        self.routes.append(r)
        #trigger route selection
    
    def flush_neighbour(self, neighbour: _Neighbour):
        self.neighbours.remove(neighbour)
        #remove routes too?


    
        