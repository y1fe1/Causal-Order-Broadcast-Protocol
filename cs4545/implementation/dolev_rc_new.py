import asyncio
import datetime
from enum import Enum
import os
import random

from datetime import datetime
from typing import Dict,List, Optional, Any

from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from cs4545.implementation.node_log import message_logger, OutputMetrics, LOG_LEVEL
from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from ..system.da_types import ConnectionMessage

class MessageConfig:
    def __init__(self, broadcasters={1:2, 2:1}, malicious_nodes=[], N = 10, msg_level = LOG_LEVEL.DEBUG):
        self.N = N
        self.broadcasters = broadcasters
        self.malicious_nodes = malicious_nodes
        self.f = len(malicious_nodes)
        self.msg_level = msg_level

class MessageType(Enum):
    SEND = 1
    ECHO = 2
    READY = 3

@dataclass(
    msg_id=3 # TODO: should this be different for different messages?
)  # The value 1 identifies this message and must be unique per community.
class DolevMessage:
    message: str
    message_id: int
    source_id: int
    path: List[int]
    phase: str = "None"
    is_delayed: bool = True

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
    def __init__(self, settings: CommunitySettings, parameters: MessageConfig=MessageConfig()) -> None:
        super().__init__(settings)
        
        if parameters.f != len(parameters.malicious_nodes):
            print("Warning: f should be equal to the length of malicious_nodes")
        
        self.N = parameters.N
        self.f = parameters.f
        
        self.connectivity = len(self.get_peers())
        self.starter_nodes = parameters.broadcasters #broadcasters
        self.malicious_nodes = parameters.malicious_nodes

        #assume no malicious node exist rn
        self.is_malicious: bool = False #(self.node_id in self.malicious_nodes) 
        self.malicious_behaviour = None

        for mal_node in self.malicious_nodes:
            if(mal_node in self.starter_nodes):
                self.malicious_behaviour = "generate_fake_msg"
            else: 
                self.malicious_behaviour = "modify_msg_id"

        self.is_delivered: dict[int, bool] = {}
        self.delivered_neighbour: dict[int, set[int]] = {}
        self.message_paths: dict[int, set[tuple]] = {}
        self.message_broadcast_cnt = 0

        #optimization control vairable
        self.MD1 = True
        self.MD2 = True
        self.MD3 = True
        self.MD4 = False
        self.MD5 = False

        self.add_message_handler(DolevMessage, self.on_message)
        
        # log related stuffs
        self.node_outputMetrics = OutputMetrics(self)
        self.msg_level = parameters.msg_level
        self.metrics = DolevMetrics()

    def gen_output_file_path(self, test_name: str ="Dolev_Test") : 
        '''
            To be fair this should be part of the parent class function to Insert the subfolder directory
            This function will set the output file to be output/{test_name}_{time_stamp}/node-{node_id}.out
        '''

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")  #this time stamp may need to be sync across all the nodes, keep it at minute level would be fine ig
        subdirectory_name = f"{test_name}_{timestamp}"

        return (self.algortihm_output_file.parent 
                                      / subdirectory_name
                                      / self.algortihm_output_file.name)
    
    def generate_message_id(self, msg: str) -> int:
        self.message_broadcast_cnt += 1
        return self.node_id * 169 + self.message_broadcast_cnt * 13 + (hash(msg) % 997)
    
    def generate_message(self) -> DolevMessage:
        msg =  ''.join([random.choice(['Y', 'M', 'C', 'A']) for _ in range(4)])
        id = self.generate_message_id(msg)
        return DolevMessage(msg, id, self.node_id, [])
    
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
    
    def init_logger(self):

        self.connectivity = len(self.get_peers()) # seems like we have to recheck connectivity

        self.msg_log.log_metrics = OutputMetrics(self)
        self.msg_log.logger.setLevel(self.msg_level.value)

        self.msg_log.update_log_path(self.gen_output_file_path())
        self.msg_log.log(LOG_LEVEL.INFO, f"Message Log Init Succesfully, with Node {self.node_id}, Output_Path {self.algortihm_output_file}")

    async def on_start(self):

        self.init_logger()

        if self.node_id in self.malicious_nodes:
            self.is_malicious = True
            self.msg_log.log(LOG_LEVEL.INFO, f"Hi I am malicious {self.node_id}")

        all_ready = False
        # print(f"[Node {self.node_id}] Starting algorithm with peers {[x.address for x in self.get_peers()]} and {self.nodes}")
        while not all_ready:

            all_ready = all(
                state == "ready"
                for node_id, state in self.node_states.items()
            )

            for peer in self.get_peers():
                self.ez_send(peer, ConnectionMessage(self.node_id, "ready"))

            if not all_ready:
                self.msg_log.log(LOG_LEVEL.DEBUG, f"Node {self.node_id} waiting, states={self.node_states}")
                await asyncio.sleep(2) # this is enough to make the logic stack look happy
            
            else:
                self.msg_log.log(LOG_LEVEL.INFO, f"[Node {self.node_id}] is ready")
                self.msg_log.log(LOG_LEVEL.DEBUG, f"[Node {self.node_id}] ready, states={self.node_states}")
                self.msg_log.log(LOG_LEVEL.DEBUG, f"[Node {self.node_id}] peers: {[x.address for x in self.get_peers()]}")

        if self.node_id in self.starter_nodes:
            self.msg_log.log(LOG_LEVEL.INFO, f"[Node {self.node_id}] is starting.")
            await self.on_start_as_starter()

    async def on_start_as_starter(self):
        # By default we broadcast a message as starter, but everyone should be able to trigger a broadcast as well.
        self.msg_log.log(LOG_LEVEL.DEBUG, f"[Node {self.node_id}] entering on_start_as_starter")

        message = self.generate_message()
        self.msg_log.log(LOG_LEVEL.INFO, f"[Node {self.node_id}] Generated message: {message}")
        await self.on_broadcast(message)


    async def on_broadcast(self, message: DolevMessage) -> None:
        # Assuming everything has been set up well for this node (delivered, paths, ...)

        self.msg_log.log(LOG_LEVEL.INFO, f"[Node {self.node_id}] is starting Dolev's protocol")

        peers = self.get_peers()

        self.msg_log.log(LOG_LEVEL.DEBUG, f"[Node {self.node_id}] entering on_broadcast, Peers count: {len(peers)}")

        #if the node is a malicious node, then generate a fake msg to deliver to maximum f 
        if self.is_malicious :
            max_broadcast_cnt = self.f
            message = self.execute_mal_process(message)
        else:
            max_broadcast_cnt = len(peers)
        try:
            for peer in peers[:max_broadcast_cnt]:
                peer_id = self.node_id_from_peer(peer)
                broad_cast_log = f"[Node {self.node_id}] Broadcast Message: {message.message_id} , {message.phase} to node {peer_id}"
                self.msg_log.log(LOG_LEVEL.DEBUG,broad_cast_log)
                
                self.ez_send(peer, message)

        except Exception as e:
            self.msg_log.log(LOG_LEVEL.ERROR, f"Error in on_broadcast: {e}")
            raise e
        
        self.msg_log.log(LOG_LEVEL.INFO, f"[Node {self.node_id}] delivered self-broadcasted message {message.message_id}")
        await self.trigger_delivery(message)

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        self.is_malicious = (self.node_id in self.malicious_nodes)

        sender_id = self.node_id_from_peer(peer)
        source_id, message_id, msg_path = payload.source_id,payload.message_id,payload.path

        # if the node is malicious, it will modify the msg
        new_payload = self.generate_relay_message(payload)

        if self.MD5 and self.is_delivered.get(message_id):  #if msg is delivered already, it can be discarded

            MD5_log = f"MD5: [Node {self.node_id}] received a msg already delivered, can be discarded"
            self.msg_log.log(LOG_LEVEL.DEBUG,MD5_log)
            
            return

        if self.MD4 and self.delivered_neighbour.get(message_id) and sender_id in self.delivered_neighbour.get(message_id) :  #if msg is from a delivered neighbour, it can be dsicarded
            
            MD4_log = f"MD4: [Node {self.node_id}] received a msg {payload.phase} from delivered neighbour, can be discarded"
            self.msg_log.log(LOG_LEVEL.DEBUG,MD4_log)
            return

        # increment log cnt for this message
        self.log_message_cnt(message_id)

        if self.MD3 and not msg_path:   #if msg_path is empty, indicate the sender has delivered the msg (#MD2)

            self.delivered_neighbour.setdefault(message_id, set()).add(sender_id)
            #remove all paths in the path that contains the sender since its delivered and can be discarded
            if self.message_paths.get(message_id):
                updated_paths = set(tuple([path for path in self.message_paths.get(message_id) if sender_id not in path]))
                self.message_paths[message_id] = updated_paths

            MD3_log = f"MD3: [Node {self.node_id} received msg with empty path from delivered node {sender_id}]"
            self.msg_log.log(LOG_LEVEL.DEBUG, MD3_log)

        try:
            new_path = msg_path + [sender_id]

            recieved_log = f"[Node {self.node_id}] Got message: {payload.phase} - {new_payload.message} from node: {sender_id} with path {new_path}"
            self.msg_log.log(LOG_LEVEL.INFO,recieved_log)

            self.set_metics_start_time(new_payload.message_id)

            self.message_paths.setdefault(new_payload.message_id, set()).add(tuple(new_path))
            self.msg_log.log(LOG_LEVEL.DEBUG, f'Node {self.node_id}, {payload.message_id} message paths: {self.message_paths}')
            
            #MD1 If a process preceives a content directly from the source s, then p directly delivers it.
            if self.MD1 and not self.is_malicious and not self.is_delivered.get(message_id) and sender_id == source_id:

                MD1_log = f"MD1: [Node {self.node_id}] is a direct neighbour of Sender {sender_id} for the message {message_id}, it will be delivered"
                self.msg_log.log(LOG_LEVEL.DEBUG, MD1_log)

                await self.trigger_delivery(new_payload)

            #if len(self.message_paths.get(payload.message_id)) >= (self.f + 1): history line remaining, will be removed

            #if the node is not malicious and not delivered and there is f+1 disjoint_path_

            # if not self.is_malicious and not self.is_delivered.get(message_id) and self.new_find_disjoint_paths_ok(message_id):

            
            if not self.is_malicious and not self.is_delivered.get(message_id) and self.find_disjoint_paths_ok(message_id):
                # print(f"Node {self.node_id} has enough node-disjoint paths, delivering message: {payload.message}")
                disjoint_path_find_log = f"[Node {self.node_id}] Enough node-disjoint paths found for {message_id}, message will be delivered"
                self.msg_log.log(LOG_LEVEL.INFO, disjoint_path_find_log)

                await self.trigger_delivery(new_payload)

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
                if self.MD2 and self.is_delivered.get(message_id) and len(new_path) != 0 :
                    MD2_log = f"MD2: [Node {self.node_id}] condition met, msg {message_id} delivered, it will not be send to its neighbour]"
                    self.msg_log.log(LOG_LEVEL.DEBUG, MD2_log)
                    break

                if payload.is_delayed and (neighbor_id not in node_to_skip):

                    msg_log = f"[Node {self.node_id}] Sent message to node {neighbor_id} with path {new_path} : {payload.message}"
                    self.msg_log.log(LOG_LEVEL.INFO, msg_log)

                    payload.message = new_payload.message
                    payload.message_id = new_payload.message_id
                    payload.path = new_path

                    self.ez_send(neighbor, payload)
           
        except Exception as e:
            self.msg_log.log(LOG_LEVEL.ERROR, f"Error in on_message: {e}")
            raise e

    def generate_relay_message(self, payload: DolevMessage) -> DolevMessage:
        if self.is_malicious and (self.node_id not in self.starter_nodes):
            return self.execute_mal_process(payload)
        else: 
            return payload
            
    async def trigger_delivery(self, message: DolevMessage):
        try:
            if self.is_malicious:
                self.msg_log.log(LOG_LEVEL.WARNING, "I am malicious!!!! Why can I deliver!")
                if self.node_id == message.source_id:
                    self.msg_log.log(LOG_LEVEL.WARNING, "Never mind. It's my own message.")

            self.is_delivered.update({message.message_id: True })
            self.write_metrics(message.message_id)
            
            for msg_id, status in self.is_delivered.items():
                self.msg_log.log(LOG_LEVEL.DEBUG, f"Delivered Messages: Message ID: {msg_id}, Message Type: {message.phase}, Delivered: {status}")

            #write output to the file output
            self.msg_log.flush()
        except Exception as e:
            self.msg_log.log(LOG_LEVEL.ERROR, f"Error in trigger_delivery: {e}")
            raise e    
    
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

    # region Loggin Functions
    def log_message_cnt(self, message_id):
        self.msg_log.log_message_cnt(message_id)

    def set_metics_start_time(self, msg_id):
       self.msg_log.set_metric_start_time(msg_id)
        
    def set_metric_end_time(self,msg_id):
        self.msg_log.set_metric_end_time(msg_id)

    def log_delivered_status(self, message_id, status=True):
        self.msg_log.set_metric_delivered_status(message_id, True)

    def log_message_history(self):
        self.msg_log.set_message_history(len(self._message_history), self._message_history.bytes_sent())

    def write_metrics(self, message_id):
        self.log_delivered_status(message_id, True)
        #self.set_metric_end_time(message_id)
        self.log_message_history()
        
    def metrics_init(self):
        self.metrics.node_count = len(self.nodes)
        self.metrics.byzantine_count = len(self.malicious_nodes)
        self.metrics.connectivity = len(self.get_peers())
        self.metrics.message_count = 0
    #endregion