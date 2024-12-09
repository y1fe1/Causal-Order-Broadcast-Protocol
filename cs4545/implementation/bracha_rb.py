import datetime
import logging
import random
import math

from typing import Dict,List
from enum import Enum

from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer
from hashlib import sha256

from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from cs4545.implementation.dolev_rc_new import BasicDolevRC, MessageConfig, DolevMessage
from cs4545.implementation.node_log import message_logger, OutputMetrics, LOG_LEVEL

class BrachaConfig(MessageConfig):
    def __init__(self, broadcasters = {1:2, 2:1}, malicious_nodes = [3],N = 10, msg_level = logging.DEBUG):
        super().__init__(broadcasters, malicious_nodes,N,msg_level)

#region Message Definition
class MessageType(Enum):
    SEND = 1
    ECHO = 2
    READY = 3

@dataclass(
    msg_id=4
) 
class SendMessage(DolevMessage):

    msg_type = MessageType.SEND

    def __init__(self, message: str, source_id:int, path: List[int] , message_id: str = "3", msg_type: MessageType = MessageType.SEND):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

@dataclass(
    msg_id=5
) 
class EchoMessage(DolevMessage):

    msg_type = MessageType.ECHO

    def __init__(self, message: str, source_id:int, path , message_id: str = "3", msg_type = MessageType.ECHO):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

@dataclass(
    msg_id=6
) 
class ReadyMessage(DolevMessage):

    msg_type = MessageType.READY

    def __init__(self, message: str, source_id, path, message_id: str = "3", msg_type = MessageType.READY):
        super().__init__(message, message_id, source_id, path)
        self.msg_type = msg_type

#endregion

class BrachaRB(BasicDolevRC):
    def __init__(self, settings: CommunitySettings, parameters = BrachaConfig()) -> None:

        super().algortihm_output_file = self.gen_output_file_path()

        super().__init__(settings,parameters)

        # f should be < N/3

        self.echo_count:    dict[str, int]  = {}   # message_id -> echo list
        self.is_echo_sent: dict[str, List[bool]] = {}     # message_id -> list of node which send Echo Msg

        self.ready_count:   dict[str, int]  = {}   # message_id -> ready count
        self.is_ready_sent: dict[str, List[bool]] = {}   # message_id -> is READY message sent

        # this seems conflicting with 
        self.is_delivered:  dict[str, bool] = {}   # message_id -> is Delivered 

        self.add_message_handler(SendMessage, self.on_send)
        self.add_message_handler(EchoMessage, self.on_echo)
        self.add_message_handler(ReadyMessage, self.on_ready)


    def gen_output_file_path(self, test_name: str ="Bracha_Test") : 
        super().gen_output_file_path(test_name)

    def generate_message(self) -> SendMessage:
        msg =  ''.join([random.choice(['uk', 'pk', 'mkk', 'fk']) for _ in range(6)])
        id = sha256(msg.encode()).hexdigest()
        return SendMessage(msg, id, self.node_id, [])
    
    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        return await super().on_start_as_starter()
    
    # event <Bracha, Broadcast | M >  do
    async def on_broadcast(self, message: DolevMessage) -> None:
        #⟨Dolev,Broadcast|[Send,m]⟩
        super().on_broadcast(message)

    #trigger ⟨al,Send | q,[ECHO,m]⟩ 
    async def trigger_send_echo(self, message_id: str, count: int, threshold: int, payload: SendMessage):

        sent_echo = self.is_echo_sent.get(message_id, {}).get(self.node_id, False)

        if not sent_echo and count >= threshold:

            self.is_echo_sent.setdefault(message_id, {})[self.node_id] = True

            self.msg_log.log(LOG_LEVEL.DEBUG, f'Sent ECHO messages: {message_id}')

        # Broadcast ECHO message to peers ⟨Dolev,Broadcast|[Echo,m]⟩
        super().on_broadcast(EchoMessage(payload.message, payload.message_id, self.node_id, []))

    
    #event ⟨al,Deliver | p,[SEND,m]⟩
    @message_wrapper(SendMessage)
    async def on_send(self, peer: Peer, payload: SendMessage):

        self.msg_log.log(LOG_LEVEL.DEBUG, f'Received a SEND  message: {payload.message_id}.')

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

            self.msg_log.log(LOG_LEVEL.DEBUG, f'Sent READY messages: {message_id}')
        
        # Broadcast READY message to peers ⟨Dolev,Broadcast|[ready,m]⟩
        super().on_broadcast(ReadyMessage(payload.message, payload.message_id, self.node_id, []))

    # upon event ⟨al,Deliver | p,[ECHO,m]⟩ do
    @message_wrapper(EchoMessage)
    async def on_echo(self, peer: Peer, payload: EchoMessage):
        
        self.msg_log.log(LOG_LEVEL.DEBUG, f'Received an ECHO message: {payload.message_id}.')
        
        self.echo_count.setdefault(payload.message_id, 0)
        self.echo_count[payload.message_id] += 1

        # upon event echos.size() ≥ ⌈N+f+1⌉ and not sentReady do
        threshold = math.ceil((self.f + self.N + 1) / 2)
        await self.trigger_send_ready(payload.message_id, self.echo_count[payload.message_id], threshold, payload)

            
    #upon event ⟨al,Deliver | p,[READY,m]⟩ do
    @message_wrapper(ReadyMessage)
    async def on_ready(self, peer: Peer, payload: ReadyMessage):

        self.msg_log.log(LOG_LEVEL.DEBUG, f'Received a READY message: {payload.message_id}.')

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
    async def trigger_delivery(self, payload: DolevMessage):

        self.msg_log.log(LOG_LEVEL.DEBUG,f'Delivered a message: {payload.message_id}.')

        await self.msg_log.flush()
        
        

        



        
        