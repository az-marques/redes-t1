from Neighbour import Neighbour
from Source import Source
from RepeatedTimer import RepeatedTimer
from BabelSpeaker import BabelSpeaker

class Route():
    def __init__(self, speaker: BabelSpeaker, source: Source, neighbour: Neighbour, metric, seqno, next_hop, selected, interval) -> None:
        self.speaker = speaker
        self.source = source
        self.neighbour = neighbour
        self.metric = metric
        self.seqno = seqno
        self.next_hop = next_hop
        self.selected = selected

        self.expiry_timer = RepeatedTimer(interval*3.5, self._expiry, [self])

    def index(self):
        return self.source.prefix, self.source.plen, self.neighbour

    def compare_index(self, prefix, plen, neighbour) -> bool:
        return prefix == self.source.prefix and self.source.plen and neighbour == self.neighbour
    
    #gotta improve this, this is just comparing the start of strings. Needs to turn them into binary or at least split off each section, IE right now this returns that "123.123.123.123" matches the prefix "123.1".
    def compare_address(self, address):
        if self.source.prefix == address[:len(self.source.prefix)]:
            return len(self.source.prefix), self.next_hop
        return 0, None
    
    def _expiry(self):
        if self.metric < float('inf'): #work out a consistent definition of infinity later
            self.metric = float('inf')
        else:
            self.expiry_timer.stop()
            self.speaker.flush_route(self)
