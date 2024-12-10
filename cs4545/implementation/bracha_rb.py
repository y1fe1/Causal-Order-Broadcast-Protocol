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
    def __init__(self, broadcasters={1: 2, 2: 1}, malicious_nodes=[3], N=10, msg_level=logging.DEBUG):
        assert(len(malicious_nodes) < N / 3)
        super().__init__(broadcasters, malicious_nodes, N, msg_level)
        self.Optim1 = False
        self.Optim2 = False
        self.Optim3 = False

#region Message Definition
class MessageType(Enum):
    SEND = 1
    ECHO = 2
    READY = 3


#@dataclass(msg_id=4)
class SendMessage(DolevMessage):
    msg_type = MessageType.SEND


#@dataclass(msg_id=5)
class EchoMessage(DolevMessage):
    msg_type = MessageType.ECHO


#@dataclass(msg_id=6)
class ReadyMessage(DolevMessage):
    msg_type = MessageType.READY



# endregion

class BrachaRB(BasicDolevRC):
    def __init__(self, settings: CommunitySettings, parameters=BrachaConfig()) -> None:

        super().__init__(settings, parameters)

        # f should be < N/3

        self.echo_count: dict[str, int] = {}  # message_id -> echo list
        self.is_echo_sent: dict[str, List[bool]] = {}# message_id -> list of node which send Echo Msg

        self.ready_count: dict[str, int] = {}  # message_id -> ready count
        self.is_ready_sent: dict[str, List[bool]] = {}# message_id -> is READY message sent

        # this seems conflicting with
        self.is_delivered: dict[str, bool] = {}  # message_id -> is Delivered

        self.add_message_handler(SendMessage, self.on_send)
        self.add_message_handler(EchoMessage, self.on_echo)
        self.add_message_handler(ReadyMessage, self.on_ready)
        
        self.Optim1 = parameters.Optim1
        self.Optim2 = parameters.Optim2
        self.Optim3 = parameters.Optim3

    def gen_output_file_path(self, test_name: str = "Bracha_Test"):
        super().gen_output_file_path(test_name)

    def generate_message(self) -> SendMessage:
        msg = "".join([random.choice(["uk", "pk", "mkk", "fk"]) for _ in range(6)])
        id = sha256(msg.encode()).hexdigest()
        return SendMessage(msg, id, self.node_id, [])

    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        await super().on_start_as_starter()

    # event <Bracha, Broadcast | M >  do
    async def on_broadcast(self, message: DolevMessage) -> None:
        # ⟨Dolev,Broadcast|[Send,m]⟩
        super().on_broadcast(message)

    
    #event ⟨al,Deliver | p,[SEND,m]⟩
    @message_wrapper(SendMessage)
    async def on_send(self, peer: Peer, payload: SendMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received a SEND message: {payload.message_id}.")
        # upon event ⟨al,Deliver | p,[SEND,m]⟩ and not sentEcho do
        # threshold = math.ceil((self.f + self.N + 1) / 2)
        # await self.trigger_send_echo(message_id, self.echo_count[message_id], threshold, payload)
        await self.trigger_send_echo(payload.message_id, payload)

    # upon event ⟨al,Deliver | p,[ECHO,m]⟩ do
    @message_wrapper(EchoMessage)
    async def on_echo(self, peer: Peer, payload: EchoMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received an ECHO message: {payload.message_id}.")
        # echos.insert(p)
        self.increment_echo_count(payload.message_id)
        # upon event echos.size() ≥ ⌈N+f+1⌉ and not sentReady do
        threshold = math.ceil((self.f + self.N + 1) / 2)
        await self.trigger_send_ready(payload.message_id, self.echo_count[payload.message_id], threshold, payload)
        await self.Optim1_handler(payload.message_id, payload, MessageType.ECHO)


    # upon event ⟨al,Deliver | p,[READY,m]⟩ do
    @message_wrapper(ReadyMessage)
    async def on_ready(self, peer: Peer, payload: ReadyMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received a READY message: {payload.message_id}.")
        self.increment_ready_count(payload.message_id)
        # upon event readys.size() ≥ f+1 and not sentReady do
        threshold = self.f + 1
        await self.trigger_send_ready(payload.message_id, self.ready_count[payload.message_id], threshold, payload)

        # upon event readys.size() ≥ 2f+1 and not delivered do
        self.trigger_delivery_if_ready(payload)
        
        await self.Optim1_handler(payload.message_id, payload, MessageType.ECHO)


    def broadcast_message(self, message_id: str, msg_type: MessageType, payload: DolevMessage, set_flag: bool = False):
        if set_flag:
            if msg_type == MessageType.ECHO:
                self.set_echo_sent_true(message_id)
            elif msg_type == MessageType.READY:
                self.set_ready_sent_true(message_id)
                
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Sent {msg_type.name} messages: {message_id}")
        
        if msg_type == MessageType.SEND:
            super().on_broadcast(EchoMessage(payload.message, payload.message_id, self.node_id, []))
        elif msg_type == MessageType.ECHO:
            super().on_broadcast(EchoMessage(payload.message, payload.message_id, self.node_id, []))
        elif msg_type == MessageType.READY:
            super().on_broadcast(ReadyMessage(payload.message, payload.message_id, self.node_id, []))

            
    """
    Triggers
    """

    ####trigger ⟨al,Send | q,[ECHO,m]⟩
    # upon event ⟨al, Deliver | p, [SEND, m]⟩ and not sentEcho do
    #   sentEcho = True
    #   forall q do { trigger ⟨al, Send | q, [ECHO, m]⟩ }
    async def trigger_send_echo(self, message_id: str, payload: SendMessage):
        sent_echo = self.check_if_echo_sent(message_id)
        # if not sent_echo and count >= threshold:
        if not sent_echo:
            self.broadcast_message(message_id, MessageType.ECHO, payload, set_flag=True)
            # self.is_echo_sent.setdefault(message_id, {})[self.node_id] = True
            # self.msg_log.log(LOG_LEVEL.DEBUG, f"Sent ECHO messages: {message_id}")
            # # Broadcast ECHO message to peers ⟨Dolev,Broadcast|[Echo,m]⟩
            # super().on_broadcast(
            #     EchoMessage(payload.message, payload.message_id, self.node_id, [])
            # )

    # trigger ⟨al,Send | q,[READY,m]⟩
    async def trigger_send_ready(self, message_id: str, count: int, threshold: int, payload: EchoMessage):
        """
        Triggers sending a READY message if the conditions are met.
        Ensures the payload is of a valid type and processes it accordingly.
        """
        sent_ready = self.check_if_ready_sent(message_id)
        if not sent_ready and count >= threshold:
            self.broadcast_message(message_id, MessageType.READY, payload, set_flag=True)
            # self.is_ready_sent.setdefault(message_id, {})[self.node_id] = True
            # self.msg_log.log(LOG_LEVEL.DEBUG, f"Sent READY messages: {message_id}")
            # # Broadcast READY message to peers ⟨Dolev,Broadcast|[ready,m]⟩
            # super().on_broadcast(
            #     ReadyMessage(payload.message, payload.message_id, self.node_id, [])
            # )
    
    def trigger_delivery_if_ready(self, payload):
        if (not self.is_delivered.get(payload.message_id)
            and self.ready_count.get(payload.message_id) >= 2 * self.f + 1
        ):
            self.is_delivered.setdefault(payload.message_id, True)
            self.trigger_delivery(payload)
            
    # trigger ⟨Bracha,Deliver | s,m⟩
    async def trigger_delivery(self, payload: DolevMessage):

        
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Delivered a message: {payload.message_id}.")
        await self.msg_log.flush()
        
    """
    Optimizations
    """
    
    def Optim1_handler(self, message_id: str, payload: EchoMessage, msg_type: MessageType):
        if self.Optim1:
            count = 0
            threshold = 0
            if msg_type == MessageType.ECHO:
                count = self.echo_count[message_id]
                threshold = self.f + 1
                if count >= threshold:
                    if not self.check_if_echo_sent(message_id):
                        self.set_echo_sent_true(message_id)
                        self.broadcast_message(message_id, MessageType.ECHO, payload, True)
            elif msg_type == MessageType.READY:
                if ():# TODO: 同时满足生成 ECHO 和 READY 消息的条件
                    self.set_echo_sent_true(message_id)
                    self.set_ready_sent_true(message_id)
                    self.broadcast_message(message_id, MessageType.READY, payload, True)
                elif not self.check_if_echo_sent(message_id):
                    self.set_echo_sent_true(message_id)
                    self.broadcast_message(message_id, MessageType.ECHO, payload, True)

    """
    Getter & Setter
    """
    def set_echo_sent_true(self, message_id):
        self.is_echo_sent.setdefault(message_id, {})[self.node_id] = True

    def check_if_echo_sent(self, message_id):
        sent_echo = self.is_echo_sent.get(message_id, {}).get(self.node_id, False)
        return sent_echo
    
    def check_if_ready_sent(self, message_id):
        return self.is_ready_sent.get(message_id, {}).get(self.node_id, False)
                
    def set_ready_sent_true(self, message_id):
        self.is_ready_sent.setdefault(message_id, {})[self.node_id] = True
                
    def increment_echo_count(self, message_id):
        self.echo_count.setdefault(message_id, 0)
        self.echo_count[message_id] += 1

    def increment_ready_count(self, message_id):
        self.ready_count.setdefault(message_id, 0)
        self.ready_count[message_id] += 1