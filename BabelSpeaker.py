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

        #store router ID and next hop implied by TLVs for subsequent update TLVs
        self.tlv_implied_router_id = None
        self.tlv_implied_next_hop = None
        
    def receive_tlv_hello(self, sender_address, sender_interface_id, unicast_flag, seqno, interval):
        
        neighbour = self._neighbour_acquisiton(sender_interface_id, sender_address)

        neighbour.receive_hello_from((not unicast_flag), seqno, interval)

    def receive_tlv_ihu(self, sender_address, sender_interface_id, rxcost, interval):
        
        neighbour = self._neighbour_acquisiton(sender_interface_id, sender_address)

        neighbour.receive_ihu_from(rxcost, interval)
            
    def receive_tlv_router_id(self, router_id):
        self.tlv_implied_router_id = router_id

    def receive_tlv_next_hop(self, next_hop_address):
        self.tlv_implied_next_hop = next_hop_address

    def receive_tlv_update(self, sender_interface_id, sender_address, interval, seqno, metric, plen, prefix):
        if self.tlv_implied_next_hop == None:
            raise TypeError("Next hop address not set by previous TLV")
        if self.tlv_implied_router_id == None:
            raise TypeError("Router ID not set by previous TLV")

        neighbour = self._neighbour_acquisiton(sender_interface_id, sender_address)
        source = self._source_acquisition(prefix, plen, self.tlv_implied_router_id)
        route =  self._has_route(prefix, plen, neighbour)

        #metric = self._compute_metric(neighbour, metric) uuuuhhh not sure when this should be run but apparently its not here

        is_feasible = self._is_feasible(seqno, metric)

        # When a Babel node receives an update (prefix, plen, router-id, seqno, metric) from a neighbour neigh, it checks whether it already has a route table entry indexed by (prefix, plen, neigh).
        #If no such entry exists:
        if route == None:
            #if the update is unfeasible, it MAY be ignored;
            if is_feasible:
                return
            #if the metric is infinite (the update is a retraction of a route we do not know about), the update is ignored;
            elif metric >= self.inf:
                return
            #otherwise, a new entry is created in the route table
            else:
                self._add_route(source, neighbour, seqno, metric, self.tlv_implied_next_hop)
        #If such an entry exists:
        else:
            #if the entry is currently selected, the update is unfeasible, and the router-id of the update is equal to the router-id of the entry, then the update MAY be ignored;
            if route.selected and (not is_feasible) and self.tlv_implied_router_id == route.source.router_id:
                return
            #otherwise, the entry's sequence number, advertised metric, metric, and router-id are updated
            else:
                route.seqno = seqno
                route.metric = metric

                #and if the advertised metric is not infinite, the route's expiry timer is reset to a small multiple of the interval value included in the update
                if metric < self.inf:
                    route.expiry_timer.stop()
                    route.expiry_timer.interval = interval*3.5
                    route.expiry_timer.start()

                #If the update is unfeasible, then the (now unfeasible) entry MUST be immediately unselected.
                    if not is_feasible:
                        route.selected = False 
                #"If the update caused the router-id of the entry to change, an update (possibly a retraction) MUST be sent in a timely manner as described in Section 3.7.2."
                #that's what it says in the documentation, but I don't think it's actually possible for router_id to change like this? if it did, then source wouldn't have found the source fo this route, which means this route wouldn't have been found at all
                
                #After the route table is updated, the route selection procedure is run.
                self._route_selection()

    def _route_selection(self):
        #PLACEHOLDER
        pass


    def _compute_metric(self, neighbour: Neighbour, advertised_metric):
        #PLACEHOLDER
        return advertised_metric+neighbour.cost()
    
    def _is_feasible(self, source: Source, seqno, metric):
        return source == None or metric >= self.inf or source.f_seqno<seqno or (source.f_seqno==seqno and metric<source.f_metric)

    def _has_route(self, prefix, plen, neighbour: Neighbour) -> Route:
        for r in self.routes:
            if r.compare_index(prefix, plen, neighbour):
                return r
        return None
    
    def _has_source(self, prefix, plen, router_id):
        for s in self.sources:
            if s.compare_index(prefix, plen, router_id):
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

    #looks for a neighbour with a matching interface and address, and creates one (and its interface) if one isn't found, then returns it
    def _neighbour_acquisiton(self, interface_id, address) -> Neighbour:
        interface = self._has_interface(interface_id)
        if interface == None:
            interface = Interface(interface_id)
            self.interfaces.append(interface)
        
        #can be optimized? we know there's no neighbour if we just had to make a new interface
        neighbour = self._has_neighbour(interface,address)
        if neighbour == None:
            neighbour = Neighbour(self, interface, address, None, None, None, None, None)
            self.neighbours.append(neighbour)

        return neighbour
      
    def _source_acquisition(self, prefix, plen, router_id) -> Source:
        source = self._has_source(prefix, plen, router_id)
        
        if source == None:
            source = Source(prefix, plen, router_id)
            self.sources.append(source)
        
        return source
        
    
    def flush_neighbour(self, neighbour: Neighbour):
        neighbour.mcast_timer.stop() #...I'm honestly not sure if we need to stop the timers but better safe than sorry?
        neighbour.ucast_timer.stop()
        neighbour.ihu_timer.stop()
        self.neighbours.remove(neighbour)
        #remove routes too?

    def flush_route(self, route: Route):
        route.expiry_timer.stop() #...I'm honestly not sure if we need to stop the timers but better safe than sorry?
        self.routes.remove(route)


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



    
        