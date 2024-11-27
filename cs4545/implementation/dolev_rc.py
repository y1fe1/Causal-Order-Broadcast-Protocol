import asyncio
import random
       
from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from typing import List

@dataclass(
    msg_id=3
)  # The value 1 identifies this message and must be unique per community.
class DolevMessage:
    message: str
    path: List[int]


class BasicDolevRC(DistributedAlgorithm):
    
    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.f = 3
        self.delivered = False
        self.paths: set[tuple] = set()
        self.add_message_handler(DolevMessage, self.on_message)

    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        print(f"Node {self.node_id} is starting Dolev's protocol")
        message = f"Hello world from {self.node_id}"
        self.delivered = False
        self.paths = set()

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

            if len(self.paths) >= (self.f + 1):
                if not self.delivered and self.find_disjoint_paths_ok():
                    # print(f"Node {self.node_id} has enough node-disjoint paths, delivering message: {payload.message}")
                    self.delivered = True
                    await self.trigger_delivery(payload.message)
           
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    async def trigger_delivery(self, message: str):
        print(f"Node {self.node_id} delivering message: {message}")
        self.stop()
    
    def find_disjoint_paths_ok(self) -> bool:
        if not self.paths:
            return False
        disjoint_paths = []
        used_nodes = set()
        paths_sorted = sorted(self.paths, key=len)
        
        for path in paths_sorted:
            path = path[1:]
            if not set(path).intersection(used_nodes):
                disjoint_paths.append(list(path))
                used_nodes.update(path)

                if len(disjoint_paths) >= (self.f + 1):
                    print(f"[Node {self.node_id}] Terminate, disjoint paths: {disjoint_paths}")
                    return True
        return False