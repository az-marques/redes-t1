class Source():
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