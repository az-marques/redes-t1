from Neighbour import Neighbour
from Source import Source
from Route import Route
from Interface import Interface
            
class BabelSpeaker ():
    #pending_seqno_table
    inf = float('inf') #defining this here cause we might want to change it later
    def __init__(self) -> None:
        #router id??
        self.seqno = 0
        self.interfaces = [Interface]
        self.neighbours = [Neighbour]
        self.sources = [Source]
        self.routes = [Route]
    
    def receive_tlv_hello(self, sender_address, sender_interface_id, unicast_flag, seqno, interval):
        
        sender_interface = self._has_interface(sender_interface_id)
        if sender_interface == None:
            sender_interface = Interface(sender_interface_id)
            self.interfaces.append(sender_interface)
        
        #can be optimized? we know there's no neighbour if we just had to make a new interface
        neighbour = self._has_neighbour(sender_interface,sender_address)
        if neighbour == None:
            if unicast_flag:
                neighbour = Neighbour(self, sender_interface, sender_address, None, seqno, None, interval, None)
            else:
                neighbour = Neighbour(self, sender_interface, sender_address, seqno, None, interval, None, None)
            self.neighbours.append(neighbour)

        neighbour.receive_hello_from((not unicast_flag), seqno, interval)

    def receive_tlv_ihu(self, sender_address, sender_interface_id, rxcost, interval):
        
        sender_interface = self._has_interface(sender_interface_id)
        if sender_interface == None:
            sender_interface = Interface(sender_interface_id)
            self.interfaces.append(sender_interface)
        
        #can be optimized? we know there's no neighbour if we just had to make a new interface
        neighbour = self._has_neighbour(sender_interface,sender_address)
        if neighbour == None:
            neighbour = Neighbour(self, sender_interface, sender_address, None, None, None, None, interval)
            self.neighbours.append(neighbour)

        neighbour.receive_ihu_from(rxcost, interval)
            



    def update(self, prefix, neighbour: Neighbour, router_id, seqno, advertised_metric):
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


    def _compute_metric(self, neighbour: Neighbour, advertised_metric):
        #PLACEHOLDER
        return advertised_metric+neighbour.cost()
    
    def _is_feasible(self, source, seqno, metric):
        return source == None or metric >= self.inf or source.f_seqno<seqno or (source.f_seqno==seqno and metric<source.f_metric)

    def _has_route(self, prefix, neighbour) -> Route:
        for r in self.routes:
            if Route(r).compare_index(prefix, neighbour):
                return r
        return None
    
    def _has_source(self, prefix, router_id):
        for s in self.sources:
            if Source(s).compare_index(prefix, router_id):
                return s
        return None
    
    def _has_interface(self, interface_id):
        for i in self.interfaces:
            if i.id == interface_id:
                return i
        return None

    def _has_neighbour(self, interface: Interface, address):
        for n in self.neighbours:
            if n.interface == interface and n.address == address:
                return n
        return None
  
    def _add_route(self, source: Source, neighbour: Neighbour, seqno, metric, next_hop):
        r = Route(source, neighbour, metric, seqno, next_hop, False)
        self.routes.append(r)
        #trigger route selection
    
    def flush_neighbour(self, neighbour: Neighbour):
        self.neighbours.remove(neighbour)
        #remove routes too?


    #returns the most specific currently active route for a given address, or None if there is none
    def find_route(self, address):
        greatest_match = 0
        greatest_next_hop = None

        for r in self.routes:
            if r.selected:
                match, next_hop = r.compare_address(address)
                if match > greatest_match:
                    greatest_match = match
                    greatest_next_hop = next_hop
        
        return greatest_next_hop



    
        