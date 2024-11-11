from Neighbour import Neighbour
from Source import Source

class Route():
    def __init__(self, source: Source, neighbour: Neighbour, metric, seqno, next_hop, selected) -> None:
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
    
    def compare_address(self, address):
        if self.source.prefix == address[:len(self.source.prefix)]:
            return len(self.source.prefix), self.next_hop
        return 0, None