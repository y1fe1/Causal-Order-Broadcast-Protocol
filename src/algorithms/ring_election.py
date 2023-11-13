from ipv8.community import CommunitySettings
from ipv8.types import Peer
from da_types import *
import asyncio
import random

dataclass = overwrite_dataclass(dataclass)
@dataclass(
    msg_id=1
)  # The value 1 identifies this message and must be unique per community
class ElectionMessage:
    elector: int
@dataclass(
    msg_id=2
)
class TerminationMessage:
    terminate: bool = True    
class RingElection(DistributedAlgorithm):
    """_summary_
    Implementation of Chang-Roberts algorithm, ring election in a unidirectional ring.

    Args:
        DistributedAlgorithm (_type_): _description_
    """

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.running = False
        # Make sure the register the message handlers for each message type
        self.add_message_handler(ElectionMessage, self.on_message)  # type: ignore
        self.add_message_handler(TerminationMessage, self.on_terminate)  # type: ignore

    async def on_start(self):     
        await asyncio.sleep(random.uniform(1.0, 3.0))
        if not self.running:
            peer = list(self.nodes.values())[0]
            print(f'[Node {self.node_id}] Starting by selecting a node: {self.node_id_from_peer(peer)}')
            self.ez_send(peer, ElectionMessage(self.node_id)) # type: ignore

    @lazy_wrapper(TerminationMessage) # type: ignore
    async def on_terminate(self, peer: Peer, payload: TerminationMessage) -> None: #type: ignore
        if self.running:
            _next_node_id, next_peer = [x for x in self.nodes.items() if x[1] != peer][0]
            self.ez_send(next_peer, TerminationMessage()) # type: ignore
            self.running = False
            self.stop()

    @lazy_wrapper(ElectionMessage) # type: ignore
    async def on_message(self, peer: Peer, payload: ElectionMessage) -> None: #type: ignore
        self.running = True
        # Sending it around the ring to the other peer we receveived it from
        next_node_id, next_peer = [x for x in self.nodes.items() if x[1] != peer][0]
        print(f'[Node {self.node_id}] Got a message from with elector id: {payload.elector}')

        received_id = payload.elector

        if received_id == self.node_id:
            # We are elected
            print(f'[Node {self.node_id}] we are elected!')
            print(f'[Node {self.node_id}] Sending message to terminate the algorithm!')

            self.ez_send(next_peer, TerminationMessage()) # type: ignore 
        elif received_id <  self.node_id:
            # Send self.node_id along
            self.ez_send(next_peer, ElectionMessage(self.node_id)) # type: ignore 
        else: # received_id > self.node_id
            # Send received_id along
            self.ez_send(next_peer, ElectionMessage(received_id)) # type: ignore 
 