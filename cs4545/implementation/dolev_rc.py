import asyncio
import random
       
from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer


from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from typing import List
from ..system.da_types import ConnectionMessage

@dataclass(
    msg_id=3 # TODO: should this be different for different messages?
)  # The value 1 identifies this message and must be unique per community.
class DolevMessage:
    message: str
    message_id: int
    path: List[int]

class BasicDolevRC(DistributedAlgorithm):
    
    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        
        # hardcoded here
        self.f = 2
        self.starter_nodes = [3, 4, 2]
        self.malicious_nodes = [0, 7]

       # self.is_malicious: bool = (self.node_id in self.malicious_nodes) 

        self.is_delivered: dict[int, bool] = {}
        self.message_paths: dict[int, set[tuple]] = {}
        self.message_broadcast_cnt = 0

        self.add_message_handler(DolevMessage, self.on_message)

    def generate_message_id(self, msg: str) -> int:
        self.message_broadcast_cnt += 1
        return self.node_id * 37 + self.message_broadcast_cnt + hash(msg)
    
    def generate_message(self) -> DolevMessage:
        msg =  ''.join(random.choice(['Y', 'M', 'C', 'A']))
        id = self.generate_message_id(msg)
        return DolevMessage(msg, id, [])

    async def on_start(self):
        # print(f"[Node {self.node_id}] Starting algorithm with peers {[x.address for x in self.get_peers()]} and {self.nodes}")
        if self.node_id == self.starting_node:
            # Checking if all node states are ready
            all_ready = all([x == "ready" for x in self.node_states.values()])
            while not all_ready:
                await asyncio.sleep(1)
                all_ready = all([x == "ready" for x in self.node_states.values()])
            await asyncio.sleep(1)

        if self.node_id in self.starter_nodes:
            await self.on_start_as_starter()

        print(f"[Node {self.node_id}] is ready")
        for peer in self.get_peers():
            self.ez_send(peer, ConnectionMessage(self.node_id, "ready"))

    async def on_start_as_starter(self):
        # By default we broadcast a message as starter, but everyone should be able to trigger a broadcast as well.

        message = self.generate_message()
        await self.on_broadcast(message)


    async def on_broadcast(self, message: DolevMessage) -> None:
        # Assuming everything has been set up well for this node (delivered, paths, ...)
        print(f"Node {self.node_id} is starting Dolev's protocol")
        
        for peer in self.get_peers():
            self.ez_send(peer, message)

        await self.trigger_delivery(message)

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        try:
            sender_id = self.node_id_from_peer(peer)
            # print(f"[Node {self.node_id}] Got message from node: {sender_id} with path {payload.path}")

            new_path = payload.path + [sender_id]
            #self.paths.add(tuple(new_path))
            self.message_paths.setdefault(payload.message_id, set()).add(tuple(new_path))

            for neighbor in self.get_peers():
                neighbor_id = self.node_id_from_peer(neighbor)
                if neighbor_id != self.node_id and neighbor_id not in new_path:
                    print(f"[Node {self.node_id}] Sent message to node {neighbor_id} with path {new_path} : {payload.message_id}")
                    self.ez_send(neighbor, DolevMessage(payload.message, payload.message_id, new_path))

            if len(self.message_paths.get(payload.message_id)) >= (self.f + 1):
                if not self.is_delivered.get(payload.message_id) and self.find_disjoint_paths_ok(payload.message_id):
                    # print(f"Node {self.node_id} has enough node-disjoint paths, delivering message: {payload.message}")
                    self.is_delivered[payload.message_id] = True
                    await self.trigger_delivery(payload.message)
           
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    async def trigger_delivery(self, message: DolevMessage):
        print(f"Node {self.node_id} delivering message: {message.message}")
        self.is_delivered[message.message_id] = True

    
    def find_disjoint_paths_ok(self, msg_id) -> bool:
        if not self.message_paths.get(msg_id):
            return False
        disjoint_paths = []
        used_nodes = set()
        paths_sorted = sorted(self.message_paths.get(msg_id), key=len)
        
        for path in paths_sorted:
            path = path[1:]
            if not set(path).intersection(used_nodes):
                disjoint_paths.append(list(path))
                used_nodes.update(path)

                if len(disjoint_paths) >= (self.f + 1):
                    print(f"[Node {self.node_id}] Terminate, disjoint paths: {disjoint_paths}")
                    return True
        return False
