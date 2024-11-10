from Neighbour import Neighbour
from Source import Source
from Route import Route
            
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
  
    def _add_route(self, source: Source, neighbour: Neighbour, seqno, metric, next_hop):
        r = Route(source, neighbour, metric, seqno, next_hop, False)
        self.routes.append(r)
        #trigger route selection
    
    def flush_neighbour(self, neighbour: Neighbour):
        self.neighbours.remove(neighbour)
        #remove routes too?


    #returns the currently active route for a given address
    def find_route(self, address):

        return



    
        