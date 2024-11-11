from BabelSpeaker import BabelSpeaker
from RepeatedTimer import RepeatedTimer

class Source():
    def __init__(self, speaker: BabelSpeaker, prefix, plen, router_id) -> None:
        self.speaker = speaker
        self.prefix = prefix
        self.plen = plen
        self.router_id = router_id
        self.f_seqno
        self.f_metric
        
        self.gc_timer = RepeatedTimer(180, speaker.flush_source, [self])
        self.gc_timer.start()

    def index(self):
        return self.prefix, self.plen, self.router_id
    def compare_index(self, prefix, plen, router_id) -> bool:
        return prefix == self.prefix and plen == self.plen and router_id == self.router_id