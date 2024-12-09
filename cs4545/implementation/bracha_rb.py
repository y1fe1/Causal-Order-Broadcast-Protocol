import datetime
import logging
import random
import math

from typing import List
from enum import Enum

from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from hashlib import sha256

from cs4545.implementation.node_log import message_logger, OutputMetrics, LOG_LEVL

class BrachaConfig:
    def __init__(self, broadcasters = {1:2, 2:1}, malicious_nodes = [3], f = 2, N = 10, msg_level = logging.DEBUG):
        self.broadcasters = broadcasters            # broadcaster_id -> repeated_times
        self.malicious_nodes = malicious_nodes
        self.f = f
        self.N = N

        self.msg_level = msg_level

#region Message Definition
class MessageType(Enum):
    SEND = 1
    ECHO = 2
    READY = 3

class BrachaMessage:
    def __init__(self, message: str, message_id: str, source_id: int, path: List[int]):

        self.message = message
        self.message_id = message_id

        # field required to implement dolev protocol on BRB Message
        self.source_id = source_id
        self.path = path

@dataclass(
    msg_id=3
) 
class SendMessage(BrachaMessage):

    msg_type = MessageType.SEND

    def __init__(self, message: str, source_id:int, path , message_id: str = "3", msg_type = MessageType.SEND):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

@dataclass(
    msg_id=4
) 
class EchoMessage(BrachaMessage):

    msg_type = MessageType.ECHO

    def __init__(self, message: str, source_id:int, path , message_id: str = "3", msg_type = MessageType.ECHO):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

@dataclass(
    msg_id=5
) 
class ReadyMessage(BrachaMessage):

    msg_type = MessageType.READY

    def __init__(self, message: str, source_id, path, message_id: str = "3", msg_type = MessageType.READY):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

#endregion

class BrachaRB(DistributedAlgorithm):
    def __init__(self, settings: CommunitySettings, parameters = BrachaConfig()) -> None:
        super().__init__(settings)

        self.f = parameters.f # f should be < N/3
        self.N = parameters.N

        self.connectivity = len(self.get_peers())

        self.broadcasters = parameters.broadcasters
        self.malicious_nodes = parameters.malicious_nodes
        
        self.echo_count:    dict[str, int]  = {}   # message_id -> echo list
        self.is_echo_sent: dict[str, List[bool]] = {}     # message_id -> list of node which send Echo Msg

        self.ready_count:   dict[str, int]  = {}   # message_id -> ready count
        self.is_ready_sent: dict[str, List[bool]] = {}   # message_id -> is READY message sent

        self.is_delivered:  dict[str, bool] = {}   # message_id -> is Delivered

        self.add_message_handler(SendMessage, self.on_send)
        self.add_message_handler(EchoMessage, self.on_echo)
        self.add_message_handler(ReadyMessage, self.on_ready)

        node_outputMetrics = OutputMetrics(self)
        self.algortihm_output_file = self.gen_output_file_path()

        self.msg_log = message_logger(self.node_id,parameters.msg_level, self.algortihm_output_file,node_outputMetrics)

    def gen_output_file_path(self, test_name: str ="Bracha_Test") : 

        '''
            To be fair this should be part of the parent class function to Insert the subfolder directory
            This function will set the output file to be output/{test_name}_{time_stamp}/node-{node_id}.out
        '''

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  #this time stamp may need to be sync across all the nodes
        subdirectory_name = f"{test_name}_{timestamp}"

        return (self.algorithm_output_file.parent 
                                      / subdirectory_name
                                      / self.algortihm_output_file.name)

    def generate_message(self) -> SendMessage:
        msg =  ''.join([random.choice(['uk', 'pk', 'mkk', 'fk']) for _ in range(6)])
        id = sha256(msg.encode()).hexdigest()
        return SendMessage(msg, id, self.node_id, [])
    
    async def on_start(self):
       
        self.msg_log.log(LOG_LEVL.INFO,  f'Node {self.node_id} is starting.')

        if self.node_id in self.broadcasters.keys():
            for _ in range(self.broadcasters[self.node_id]):
                await self.on_broadcast()


    #region DolevProtocol


    # ⟨Dolev,Broadcast|[mType,m]⟩ broadcast a message along a non-fully connected network following Dolev Protocol
    async def dolev_broadcast(self, message: BrachaMessage) -> None:

        self.msg_log.log(LOG_LEVL.INFO, f"Node {self.node_id} is starting Dolev's protocol")

        peers = self.get_peers()

        self.msg_log.log(LOG_LEVL.DEBUG, f"Node {self.node_id} entering on_broadcast, Peers count: {len(peers)}")

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
                self.msg_log.log(LOG_LEVL.DEBUG,broad_cast_log)

                self.ez_send(peer, message)

        except Exception as e:

            self.msg_log.log(LOG_LEVL.ERROR, f"Error in dolev_broadcast with node {self.node_id}: {e}")
            raise e
        
        print(f"[Node {self.node_id}] delivered through Source Node")
        self.trigger_delivery(message)



    #endregion DolevProtocol

    # event <Bracha, Broadcast | M >  do
    async def on_broadcast(self) -> None:
        
        self.msg_log.log(LOG_LEVL.INFO,f'Node {self.node_id} is broadcasting.')
        
        message = self.generate_message()

        for peer in self.get_peers():
            self.ez_send(peer, message)

    #trigger ⟨al,Send | q,[ECHO,m]⟩ 
    async def trigger_send_echo(self, message_id: str, count: int, threshold: int, payload: SendMessage):

        sent_echo = self.is_echo_sent.get(message_id, {}).get(self.node_id, False)

        if not sent_echo and count >= threshold:

            self.is_echo_sent.setdefault(message_id, {})[self.node_id] = True

            self.msg_log.log(LOG_LEVL.DEBUG, f'Sent ECHO messages: {message_id}')

        # Broadcast ECHO message to peers
        for peer in self.get_peers():
            self.ez_send(peer, EchoMessage(payload.message, payload.message_id))

    
    #event ⟨al,Deliver | p,[SEND,m]⟩
    @message_wrapper(SendMessage)
    async def on_send(self, peer: Peer, payload: SendMessage):

        self.msg_log.log(LOG_LEVL.DEBUG, f'Received a SEND  message: {payload.message_id}.')

        message_id = payload.message_id
        
        # upon event ⟨al,Deliver | p,[SEND,m]⟩ and not sentEcho do
        threshold = math.ceil((self.f + self.N + 1) / 2)
        await self.trigger_send_echo(message_id, self.echo_count[message_id], threshold, payload)

    # trigger ⟨al,Send | q,[READY,m]⟩
    async def trigger_send_ready(self, message_id: str, count: int, threshold: int, payload: EchoMessage):
        """
        Triggers sending a READY message if the conditions are met.
        Ensures the payload is of a valid type and processes it accordingly.
        """

        sent_ready = self.is_ready_sent.get(message_id, {}).get(self.node_id, False)

        if not sent_ready and count >= threshold:
            self.is_ready_sent.setdefault(message_id, {})[self.node_id] = True

            self.msg_log.log(LOG_LEVL.DEBUG, f'Sent READY messages: {message_id}')
        
        for p in self.get_peers():
                self.ez_send(p, ReadyMessage(payload.message, payload.message_id))

    # upon event ⟨al,Deliver | p,[ECHO,m]⟩ do
    @message_wrapper(EchoMessage)
    async def on_echo(self, peer: Peer, payload: EchoMessage):
        
        self.msg_log.log(LOG_LEVL.DEBUG, f'Received an ECHO message: {payload.message_id}.')
        
        self.echo_count.setdefault(payload.message_id, 0)
        self.echo_count[payload.message_id] += 1

        # upon event echos.size() ≥ ⌈N+f+1⌉ and not sentReady do
        threshold = math.ceil((self.f + self.N + 1) / 2)
        await self.trigger_send_ready(payload.message_id, self.echo_count[payload.message_id], threshold, payload)

            
    #upon event ⟨al,Deliver | p,[READY,m]⟩ do
    @message_wrapper(ReadyMessage)
    async def on_ready(self, peer: Peer, payload: ReadyMessage):

        self.msg_log.log(LOG_LEVL.DEBUG, f'Received a READY message: {payload.message_id}.')

        self.ready_count.setdefault(payload.message_id, 0)
        self.ready_count[payload.message_id] += 1

        # upon event readys.size() ≥ f+1 and not sentReady do
        threshold = self.f + 1
        await self.try_send_ready(payload.message_id, self.ready_count[payload.message_id], threshold, payload)

        # upon event readys.size() ≥ 2f+1 and not delivered do
        if not self.is_delivered.get(payload.message_id) and \
            self.ready_count.get(payload.message_id) >= 2 * self.f + 1:
            self.is_delivered.setdefault(payload.message_id, True)

            self.trigger_delivery(payload)

    # trigger ⟨Bracha,Deliver | s,m⟩
    async def trigger_delivery(self, payload: BrachaMessage):

        self.msg_log.log(LOG_LEVL.DEBUG,f'Delivered a message: {payload.message_id}.')

        await self.msg_log.flush()
        
        

        



        
        