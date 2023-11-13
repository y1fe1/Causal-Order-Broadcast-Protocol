from ipv8.community import CommunitySettings
from ipv8.types import Peer
from da_types import *

dataclass = overwrite_dataclass(dataclass)

@dataclass(
    msg_id=1
)  # The value 1 identifies this message and must be unique per community
class MyMessage:
    counter: int
class EchoAlgorithm(DistributedAlgorithm):
    """_summary_
    Simple example that just echoes messages between two nodes
    Args:
        DistributedAlgorithm (_type_): _description_
    """

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.echo_counter = 0
        self.max_echo_count = 10
        self.add_message_handler(MyMessage, self.on_message)  # type: ignore


    def on_start(self):
        if self.node_id == 1:
            #  Only node 1 starts
            peer = self.nodes[0]
            self.ez_send(peer, MyMessage(self.echo_counter)) # type: ignore


    @lazy_wrapper(MyMessage) # type: ignore
    async def on_message(self, peer: Peer, payload: MyMessage) -> None: #type: ignore
        sender_id = self.node_id_from_peer(peer)
        self.echo_counter = payload.counter + 1
        if self.echo_counter >= self.max_echo_count:
            print(f'Node {self.node_id} is stopping')
            self.stop()
        print(f'[Node {self.node_id}] Got a message from node: {sender_id}.\t current counter: {self.echo_counter}')
        # Then synchronize with the rest of the network again.
        self.ez_send(peer, MyMessage(self.echo_counter)) # type: ignore    