import asyncio
import os
import random
import time
from typing import Dict

       
from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from src.system.da_types import DistributedAlgorithm, message_wrapper
from typing import List
from ..system.da_types import ConnectionMessage


class DolevConfig:
    def __init__(self, starter_nodes=[1, 6, 0, 2], f = 0, malicious_nodes=[]):
        self.starter_nodes = starter_nodes
        self.f = f
        self.malicious_nodes = malicious_nodes

@dataclass(
    msg_id=3 # TODO: should this be different for different messages?
)  # The value 1 identifies this message and must be unique per community.
class DolevMessage:
    message: str
    message_id: int
    source_id : int
    path: List[int]

class DolevMetrics:
    node_count: int = 0
    byzantine_count: int = 0
    delivered_cnt: int = 0
    connectivity: int = 0
    message_count: int = 0
    last_message_count: int = 0
    start_time: Dict[int, float] = {}
    end_time: Dict[int, float] = {}
    latency: float = 0.0

class BasicDolevRC(DistributedAlgorithm):
    def __init__(self, settings: CommunitySettings, parameters: DolevConfig=DolevConfig()) -> None:
        super().__init__(settings)
        
        # if parameters.f != len(parameters.malicious_nodes):
        #     print("Error: f should be equal to the length of malicious_nodes! Aborting......")
        #     self.stop()
        
        self.f = parameters.f
        self.starter_nodes = parameters.starter_nodes
        self.malicious_nodes = parameters.malicious_nodes

        #assume no malicious node exist rn
        self.is_malicious: bool = False#(self.node_id in self.malicious_nodes) 
        self.malicious_behaviour = None

        for mal_node in self.malicious_nodes:
            if(mal_node in self.starter_nodes):
                self.malicious_behaviour = "generate_fake_msg"
            else : 
                self.malicious_behaviour = "modify_msg_id"

        self.is_delivered: dict[int, bool] = {}
        self.delivered_neighbour: dict[int, set[int]] = {}
        self.message_paths: dict[int, set[tuple]] = {}
        self.message_broadcast_cnt = 0

        #optimization control vairable
        self.MD1 = True
        self.MD2 = True
        self.MD3 = True
        self.MD4 = True
        self.MD5 = True

        self.add_message_handler(DolevMessage, self.on_message)
        
        self.metrics = DolevMetrics()

    def generate_message_id(self, msg: str) -> int:
        self.message_broadcast_cnt += 1
        return self.node_id * 169 + self.message_broadcast_cnt * 13 + (hash(msg) % 997)
    
    def generate_message(self) -> DolevMessage:
        msg =  ''.join([random.choice(['Y', 'M', 'C', 'A']) for _ in range(4)])
        id = self.generate_message_id(msg)
        return DolevMessage(msg, id,self.node_id,[])
    
    def generate_malicious_msg(self) -> DolevMessage:

        msg = f"fake news!"
        id = self.generate_message_id(msg)

        fake_msg_log = f"[Malicious Node {self.node_id}] generated malicious msg to send"
        self.append_output(fake_msg_log)
        print(fake_msg_log)
        
        return DolevMessage(msg,id,self.node_id,[])
    
    def mal_modify_msg(self, payload: DolevMessage) ->  DolevMessage:

        if payload:
            original_msg = payload.message
            fake_message = f"fake behaviour set on: {original_msg}"
            fake_id = hash(fake_message) # self.generate_message_id(fake_message)

        
            fake_msg_log = f"[Malicious Node {self.node_id}] tampered the original msg"
            self.append_output(fake_msg_log)
            print(fake_msg_log)

            return DolevMessage(fake_message, fake_id, payload.source_id, payload.path)

    def execute_mal_process(self, msg) -> DolevMessage:

        (behaviour,args) = {
            "generate_fake_msg" : (self.generate_malicious_msg, ()),
            "modify_msg_id" : (self.mal_modify_msg, (msg,)),
        }.get(self.malicious_behaviour, (None,None))

        try:
            if behaviour is None:
                raise ValueError("No valid behavior was selected for malicious processing.")
        
            processed_mal_msg = behaviour(*args)

        except Exception as e:
            print(f"Error in execute_mal_process: {e}")
            raise
        
        return processed_mal_msg
    


    async def on_start(self):
        if self.node_id in self.malicious_nodes:
            self.is_malicious = True
            print(f"Hi I am malicious {self.node_id}")

        if self.node_id in self.starter_nodes:
            await self.on_start_as_starter()
        print(f"[DEBUG] Node {self.node_id} starting with starter_nodes={self.starter_nodes}")

        # print(f"[Node {self.node_id}] Starting algorithm with peers {[x.address for x in self.get_peers()]} and {self.nodes}")
        if self.node_id == self.starting_node:
            # Checking if all node states are ready
            all_ready = all([x == "ready" for x in self.node_states.values()])
            while not all_ready:
                print(f"[DEBUG] Node {self.node_id} waiting, states={self.node_states}")
                await asyncio.sleep(1)
                all_ready = all([x == "ready" for x in self.node_states.values()])
                
            print(f"[DEBUG] Node {self.node_id} has received all ready states, ready to run")
            await asyncio.sleep(1)

        print(f"[DEBUG] Node {self.node_id} peers: {[x.address for x in self.get_peers()]}")
        print(f"[Node {self.node_id}] is ready")
        for peer in self.get_peers():
            self.ez_send(peer, ConnectionMessage(self.node_id, "ready"))
            

    async def on_start_as_starter(self):
        # By default we broadcast a message as starter, but everyone should be able to trigger a broadcast as well.
        print(f"[DEBUG] Node {self.node_id} entering on_start_as_starter")
        message = self.generate_message()
        print(f"[DEBUG] Generated message: {message}")
        await self.on_broadcast(message)


    async def on_broadcast(self, message: DolevMessage) -> None:
        # Assuming everything has been set up well for this node (delivered, paths, ...)
        print(f"[DEBUG] Node {self.node_id} entering on_broadcast, Peers count: {len(self.get_peers())}")
        print(f"Node {self.node_id} is starting Dolev's protocol")
        
        peers = self.get_peers()

        #if the node is a malicious node, then generate a fake msg to deliver to maximum f 
        if self.is_malicious :
            max_broadcast_cnt = self.f
            message = self.execute_mal_process(message)

        else:
            max_broadcast_cnt = len(peers)

        try:
            for peer in peers[:max_broadcast_cnt]:

                peer_id = self.node_id_from_peer(peer)

                broad_cast_log = f"[Node {self.node_id}] Sent message : {message.message_id} to node {peer_id} in broadcast"
                self.append_output(broad_cast_log)
                print(broad_cast_log)

                self.ez_send(peer, message)

        except Exception as e:
            print(f"Error in on_broadcast: {e}")
            raise e
        
        print(f"[Node {self.node_id}] delivered through Source Node")
        self.trigger_delivery(message)

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        self.is_malicious = (self.node_id in self.malicious_nodes)

        sender_id = self.node_id_from_peer(peer)
        source_id, message_id, msg_path = payload.source_id,payload.message_id,payload.path

        # if the node is malicious, it will modify the msg
        if self.is_malicious and (self.node_id not in self.starter_nodes):
            new_payload = self.execute_mal_process(payload)
        else: 
            new_payload = DolevMessage(payload.message, payload.message_id, payload.source_id, payload.path)

        if self.MD5 and self.is_delivered.get(message_id):  #if msg is delivered already, it can be discarded

            MD5_log = f"[Node {self.node_id}] received an already delivered, can be discarded"
            self.append_output(MD5_log)
            print(MD5_log)
            
            return

        if self.MD4 and self.delivered_neighbour.get(message_id) and sender_id in self.delivered_neighbour.get(message_id) :  #if msg is from a delivered neighbour, it can be dsicarded
            
            MD4_log = f"[Node {self.node_id}] received a msg from delivered neighbour, can be discarded"
            self.append_output(MD4_log)
            print(MD4_log)
            return


        if self.MD3 and not msg_path:   #if msg_path is empty, indicate the sender has delivered the msg (#MD2)

            self.delivered_neighbour.setdefault(message_id, set()).add(sender_id)
            #remove all paths in the path that contains the sender since its delivered and can be discarded
            if self.message_paths.get(message_id):
                updated_paths = set(tuple([path for path in self.message_paths.get(message_id) if sender_id not in path]))
                self.message_paths[message_id] = updated_paths

            MD3_log = f"[Node {self.node_id} received msg with empty path from delivered node {sender_id}]"
            self.append_output(MD3_log)
            print(MD3_log)

        try:
            new_path = msg_path + [sender_id]

            recieved_log = f"[Node {self.node_id}] Got message: {new_payload.message} from node: {sender_id} with path {new_path}"
            self.append_output(recieved_log)
            print(recieved_log)

            if self.metrics.start_time.get(new_payload.message_id, 0) == 0:
                self.metrics_init()
                self.set_start_time(new_payload.message_id)
            
            self.message_paths.setdefault(new_payload.message_id, set()).add(tuple(new_path))
            print(f'Node {self.node_id}, {payload.message_id}message paths: {self.message_paths}')
            
            #MD1 If a process preceives a content directly from the source s, then p directly delivers it.
            if self.MD1 and not self.is_malicious and not self.is_delivered.get(message_id) and sender_id == source_id:
                MD1_log = f"[Node] {self.node_id} is a direct neighbour of Sender {sender_id} for the message {message_id}, it will be delivered"
                self.append_output(MD1_log)
                print(MD1_log)
                print(f'Node {self.node_id} delivered through MD1')
                self.trigger_delivery(new_payload)

            #if len(self.message_paths.get(payload.message_id)) >= (self.f + 1): history line remaining, will be removed

            #if the node is not malicious and not delivered and there is f+1 disjoint_path_

            # if not self.is_malicious and not self.is_delivered.get(message_id) and self.new_find_disjoint_paths_ok(message_id):

            
            if not self.is_malicious and not self.is_delivered.get(message_id) and self.find_disjoint_paths_ok(message_id):
                # print(f"Node {self.node_id} has enough node-disjoint paths, delivering message: {payload.message}")
                self.metrics.message_count = len(self._message_history)
                
                disjoint_path_find_log = f"Enough node-disjoint paths found, message will be delivered"
                self.append_output(disjoint_path_find_log)
                print(disjoint_path_find_log)

                self.trigger_delivery(new_payload)

            #all node that can be skipped
            node_to_skip = set(new_path)
            node_to_skip.update([source_id, self.node_id])

            if self.MD3:
                if self.delivered_neighbour.get(message_id):
                    node_to_skip.update(self.delivered_neighbour.get(message_id))

            # MD.2 If a process p has delivered a message, then it can discard all the related
            # paths and relay the content only with an empty path to all of its neighbors.
            if self.MD2 and self.is_delivered.get(message_id) :
                new_path = []
                self.message_paths[message_id] = set()

            for neighbor in self.get_peers():
                neighbor_id = self.node_id_from_peer(neighbor)

                # MD2 
                if self.is_delivered.get(message_id) and len(new_path) != 0 :
                    MD2_log = f"[MD2 condition met, msg {message_id} delivered, it will not send it to its neighbour]"
                    self.append_output(MD2_log)
                    break

                if neighbor_id not in node_to_skip:
                    msg_log = f"[Node {self.node_id}] Sent message to node {neighbor_id} with path {new_path} : {payload.message}"
                    self.append_output(msg_log)

                    print(msg_log)

                    self.ez_send(neighbor, DolevMessage(new_payload.message, new_payload.message_id, source_id, new_path))
           
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    def trigger_delivery(self, message: DolevMessage):
        if self.is_malicious:
            print("I am malicious!!!! Why can I deliver!")
            if self.node_id == message.source_id:
                print("Never mind. It's my own message.")

        self.is_delivered[message.message_id] = True
        self.metrics.delivered_cnt+=1

        deliver_log = f"Node {self.node_id} delivering message: {message.message}"
        self.append_output(deliver_log)
        print(deliver_log)

        for msg_id, status in self.is_delivered.items():
            self.append_output(f"Delivered Messages: Message ID: {msg_id}, Delivered: {status}")

        self.save_algorithm_output()
        self.save_node_stats()
        
        self.get_end_time_and_latency(message.message_id)
        self.write_metrics()

    
    def find_disjoint_paths_ok(self, msg_id) -> bool:
        # TODO: Very likely to be wrong and thus causing nodes to not deliver a correct message.

        if not self.message_paths.get(msg_id):
            return False
        
        # print(f"The paths to be checked: {self.message_paths.get(msg_id)}")
        disjoint_paths = []
        used_nodes = set()
        paths_sorted = sorted(self.message_paths.get(msg_id), key=len)
        
        for path in paths_sorted:
            path = path[1:]
            if not set(path).intersection(used_nodes):
                disjoint_paths.append(list(path))
                used_nodes.update(path)

                if len(disjoint_paths) >= (self.f + 1):

                    path_log = f"[Node {self.node_id}] Terminate, disjoint paths: {disjoint_paths}" 
                    self.append_output(path_log)
                    print(path_log)
                    return True
        return False

    def new_find_disjoint_paths_ok(self, msg_id) -> bool:
        f = self.f
        sets = list(self.message_paths.get(msg_id))
        # for path in sets:
        #     path = path[1:]
        universe = set()
        for s in sets:
            universe.update(s)
        universe = sorted(universe)
        
        element_to_bit = {el: 1 << i for i, el in enumerate(universe)}
        bitmasks = []
        for s in sets:
            bitmask = 0
            for el in s:
                bitmask |= element_to_bit[el]
            bitmasks.append(bitmask)
        best_result = []
        def backtrack(index, current_subset, current_mask):
            nonlocal best_result
            if index == len(sets):
                if len(current_subset) > len(best_result):
                    best_result = current_subset[:]
                return
            backtrack(index + 1, current_subset, current_mask)
            if (current_mask & bitmasks[index]) == 0:
                current_subset.append(sets[index])
                backtrack(index + 1, current_subset, current_mask | bitmasks[index])
                current_subset.pop()
        backtrack(0, [], 0)
        return len(best_result) > f

    def set_start_time(self, msg_id):
        self.metrics.start_time[msg_id] = time.time()
        
    def get_end_time_and_latency(self, msg_id):
        self.metrics.end_time[msg_id] = time.time()
        start_time = self.metrics.start_time.get(msg_id, 0.0)

        self.metrics.latency = self.metrics.end_time.get(msg_id) - start_time
        
    def write_metrics(self):
        metrics_log = f"{self.node_id},{self.metrics.node_count},{self.metrics.byzantine_count},{self.metrics.delivered_cnt},{self.metrics.connectivity},{self.metrics.latency*1000:.03f},{self.metrics.message_count - self.metrics.last_message_count},{len(self._message_history)},{self._message_history.bytes_sent()}"
        self.metrics.last_message_count = self.metrics.message_count
        
        with open("output/metrics_output_conn"+str(self.metrics.connectivity)+".csv", "a") as f:
            f.write(metrics_log + "\n")
        
    def metrics_init(self):
        self.metrics.node_count = len(self.nodes)
        self.metrics.byzantine_count = len(self.malicious_nodes)
        self.metrics.connectivity = len(self.get_peers())
        self.metrics.message_count = 0