class Source():
    def __init__(self, prefix, plen, router_id) -> None:
        self.prefix = prefix
        self.plen = plen
        self.router_id = router_id
        self.f_seqno
        self.f_metric
        #add source garbage collection timer at some point
    def index(self):
        return self.prefix, self.plen, self.router_id
    def compare_index(self, prefix, plen, router_id) -> bool:
        return prefix == self.prefix and plen == self.plen and router_id == self.router_id