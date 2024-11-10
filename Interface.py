class Interface():
    def __init__(self, id) -> None:
        self.id = id
        self.multicast_hello_seqno = 0
    def __str__(self) -> str:
        return str(self.id)