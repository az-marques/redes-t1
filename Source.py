from BabelSpeaker import BabelSpeaker
from RepeatedTimer import RepeatedTimer

class Source():
    def __init__(self, speaker: BabelSpeaker, prefix : int, plen : int, router_id) -> None:
        self.speaker = speaker

        #the lenght of the prefix (the number after the /)
        #IE "205.16.37.32/28" -> 28
        self.plen = plen
        self._mask = ~(2**(32-self.plen)-1)

        #the IPV4 address prefix of this entry, as a 32 bit integer (with right padding zeroes)
        #IE "205.16.37.32/28" -> 11001101 00010000 00100101 0010000 (decimal 1720193680)
        self.prefix = prefix & self._mask

        self.router_id = router_id
        self.f_seqno
        self.f_metric
        
        self.gc_timer = RepeatedTimer(180, speaker.flush_source, [self])
        self.gc_timer.start()

    def index(self):
        return self.prefix, self.plen, self.router_id
    def compare_index(self, prefix, plen, router_id) -> bool:
        return prefix == self.prefix and plen == self.plen and router_id == self.router_id
    
    
    def compare_address(self,address):
        return (address & self.mask) == self.prefix