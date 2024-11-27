import asyncio
import random
       
from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from typing import List

@dataclass(
    msg_id=3 # TODO: should this be different for different messages?
)  # The value 1 identifies this message and must be unique per community.
class DolevMessage:
    message: str
    path: List[int]


class BasicDolevRC(DistributedAlgorithm):
    
    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.f = 3                   # TODO: put this in a configuration file to avoid hardcoding
        self.delivered = False
        self.paths: set[tuple] = set()
        self.add_message_handler(DolevMessage, self.on_message)

    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        # By default we broadcast a message as starter, but everyone should be able to trigger a broadcast as well.
        self.delivered = False
        self.paths = set()
        message = f"Hello world from {self.node_id}"

        await self.on_broadcast(message)


    async def on_broadcast(self, message: str) -> None:
        # Assuming everything has been set up well for this node (delivered, paths, ...)
        print(f"Node {self.node_id} is starting Dolev's protocol")
        
        for peer in self.get_peers():
            self.ez_send(peer, DolevMessage(message, []))

        await self.trigger_delivery(message)

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        try:
            sender_id = self.node_id_from_peer(peer)
            print(f"[Node {self.node_id}] Got message from node: {sender_id} with path {payload.path}")

            new_path = payload.path + [sender_id]
            self.paths.add(tuple(new_path))

            for neighbor in self.get_peers():
                neighbor_id = self.node_id_from_peer(neighbor)
                if neighbor_id != self.node_id and neighbor_id not in new_path:
                    self.ez_send(neighbor, DolevMessage(payload.message, new_path))

            if len(self.paths) >= (self.f + 1): # TODO: how to make sure the paths are disjoint?
                if not self.delivered:
                    # print(f"Node {self.node_id} has enough node-disjoint paths, delivering message: {payload.message}")
                    self.delivered = True
                    await self.trigger_delivery(payload.message)
           
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    async def trigger_delivery(self, message: str):
        print(f"Node {self.node_id} delivering message: {message}")
        self.stop()