from RepeatedTimer import RepeatedTimer

class Interface():
    def __init__(self, id) -> None:
        self.id = id
        self.multicast_hello_seqno = 0
        self.hello_timer
        self.route_update_timer
    def __str__(self) -> str:
        return str(self.id)