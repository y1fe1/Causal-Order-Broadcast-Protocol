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

from cs4545.implementation.dolev_rc_new import MessageType

class BrachaConfig(MessageConfig):
    def __init__(self, broadcasters={1:2, 2:1, 3:2}, malicious_nodes=[], N=15, msg_level=logging.DEBUG):
        assert(len(malicious_nodes) < N / 3)
        super().__init__(broadcasters, malicious_nodes, N, msg_level)
        self.Optim1 = False
        self.Optim2 = False
        self.Optim3 = False     # still not work

class BrachaRB(BasicDolevRC):
    def __init__(self, settings: CommunitySettings, parameters=BrachaConfig()) -> None:

        super().__init__(settings, parameters)

        # f should be < N/3

        self.echo_count: dict[str, set[int]] = {}  # message_id -> set of source id that entered echo states
        self.is_echo_sent: dict[str, bool] = {} # message_id -> if the node reach echo state

        self.ready_count: dict[str, set[int]] = {}  # message_id -> ready count
        self.is_ready_sent: dict[str, bool] = {}# message_id -> is READY message sent

        self.is_BRBdelivered: dict[str, bool] = {}  # message_id -> if this message has gone through SEND ECHO READY and can be BRB delivered
        
        self.Optim1 = parameters.Optim1
        self.Optim2 = parameters.Optim2
        self.Optim3 = parameters.Optim3
        
        self.Optim3_ECHO = math.ceil((self.f + self.N + 1) / 2)
        self.Optim3_READY = 2 * self.f + 1

    def gen_output_file_path(self, test_name: str = "Bracha_Test"):
        return super().gen_output_file_path(test_name)

    
    def generate_message(self) -> DolevMessage:
        msg = "".join([random.choice(["uk", "pk", "mkk", "fk"]) for _ in range(6)])
        u_id = hash(msg) % 9997
        msg_id = self.generate_message_id(msg)
        return DolevMessage(u_id, msg, msg_id, self.node_id, [], MessageType.BRACHA.value)
    
    def generate_message_id(self, msg: str) -> int:
        msg = random.shuffle(list(msg)) # randomize it so we create unique id
        self.message_broadcast_cnt += 1
        return self.node_id * 169 + self.message_broadcast_cnt * 13 + (hash(msg) % 997)
    
    def generate_phase_msg(self, og_msg, msg_type) :
        u_id, message, source_id, destination = og_msg.u_id, og_msg.message, self.node_id, []
        phase_msg_id = self.generate_message_id(message)
        if msg_type == MessageType.SEND:
            if self.Optim2:
                return DolevMessage(u_id, message, phase_msg_id, source_id, destination, msg_type.value, False)
            else:
                return DolevMessage(u_id, message, phase_msg_id, source_id, destination, msg_type.value)
        elif msg_type == MessageType.ECHO and self.is_Optim3_ECHO():
            return DolevMessage(u_id,message, phase_msg_id, source_id, destination, msg_type.value)
        elif msg_type == MessageType.READY and self.is_Optim3_READY():
            return DolevMessage(u_id, message, phase_msg_id, source_id, destination, msg_type.value)
        
    async def on_start(self):

        # sentEcho = sentReady = delivered = False echos = readys = ∅ clear them if needed
        self.echo_count.clear()
        self.is_echo_sent.clear()
        self.ready_count.clear()
        self.is_ready_sent.clear()
        self.is_BRBdelivered.clear()

        await super().on_start()

    async def on_start_as_starter(self):
        await super().on_start_as_starter()

    # event <Bracha, Broadcast | M >  do
    async def on_broadcast(self, message: DolevMessage) -> None:
        # ⟨Dolev,Broadcast|[Send,m]⟩
        await self.broadcast_message(MessageType.SEND, message)

    
    #event ⟨al,Deliver | p,[SEND,m]⟩
    async def on_send(self, payload: DolevMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received a SEND message: {payload.message_id}.")
        # upon event ⟨al,Deliver | p,[SEND,m]⟩ and not sentEcho do
        # threshold = math.ceil((self.f + self.N + 1) / 2)
        # await self.trigger_send_echo(message_id, self.echo_count[message_id], threshold, payload)
        await self.trigger_send_echo(payload)

    # upon event ⟨al,Deliver | p,[ECHO,m]⟩ do
    async def on_echo(self, payload: DolevMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received an ECHO message: {payload.message_id}.")
        
        # echos.insert(p)
        self.increment_echo_count(payload.u_id, payload.source_id)
        # upon event echos.size() ≥ ⌈N+f+1⌉ and not sentReady do
        threshold = math.ceil((self.f + self.N + 1) / 2)
        self.msg_log.log(LOG_LEVEL.DEBUG, f"echo nodes: {list(self.echo_count.values())}")
        await self.trigger_send_ready(len(list(self.echo_count.get(payload.u_id))), threshold, payload)
        await self.Optim1_handler(payload.u_id, payload, MessageType.ECHO)


    # upon event ⟨al,Deliver | p,[READY,m]⟩ do
    async def on_ready(self, payload: DolevMessage):
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Received a READY message: {payload.message_id}.")

        self.increment_ready_count(payload.u_id, payload.source_id)
        # upon event readys.size() ≥ f+1 and not sentReady do
        threshold = self.f + 1
        self.msg_log.log(LOG_LEVEL.DEBUG, f"ready nodes: {list(self.ready_count.values())}")
        await self.trigger_send_ready(len(list(self.ready_count.get(payload.u_id))), threshold, payload)

        # upon event readys.size() ≥ 2f+1 and not delivered do
        delivered_threshold = (len(self.ready_count.get(payload.u_id)) >= 2*self.f+1) \
                                and not self.is_BRBdelivered.get(payload.u_id)

        self.msg_log.log(LOG_LEVEL.DEBUG, f"threshold: {self.is_BRBdelivered.get(payload.u_id)}")
        if delivered_threshold:
            self.trigger_Bracha_Delivery(payload)
        
        await self.Optim1_handler(payload.u_id, payload, MessageType.ECHO)

    #  ⟨Dolev,Broadcast|[mType,m]⟩ ensure each msg is broadcasted to all node through dolev protocol
    async def broadcast_message(self, msg_type: MessageType, payload: DolevMessage):

        new_msg = self.generate_phase_msg(payload, msg_type)

        self.msg_log.log(LOG_LEVEL.DEBUG, f"Sent {new_msg.phase} messages: {payload.message_id}")
        await super().on_broadcast(new_msg)

            
    """
    Triggers
    """

    ####trigger ⟨al,Send | q,[ECHO,m]⟩
    # upon event ⟨al, Deliver | p, [SEND, m]⟩ and not sentEcho do
    #   sentEcho = True
    #   forall q do { trigger ⟨al, Send | q, [ECHO, m]⟩ }
    async def trigger_send_echo(self, payload: DolevMessage):
        u_id = payload.u_id
        sent_echo = self.check_if_echo_sent(u_id)
        if not sent_echo:
            self.set_echo_sent_true(u_id)
            await self.broadcast_message(MessageType.ECHO, payload)

    # trigger ⟨al,Send | q,[READY,m]⟩
    async def trigger_send_ready(self,count: int, threshold: int, payload: DolevMessage):
        u_id = payload.u_id
        """
        Triggers sending a READY message if the conditions are met.
        Ensures the payload is of a valid type and processes it accordingly.
        """
        sent_ready = self.check_if_ready_sent(u_id)
        
        self.msg_log.log(LOG_LEVEL.DEBUG, f"is_ready_sent: {sent_ready}, trigger_send_ready: {count} >= {threshold}???")

        if not sent_ready and count >= threshold:
            self.set_ready_sent_true(u_id)
            await self.broadcast_message(MessageType.READY, payload)

    # ⟨Dolev,Deliver | [source,msgType,m]⟩ 
    async def trigger_delivery(self, payload: DolevMessage):

        #self.msg_log.log(LOG_LEVEL.DEBUG, "About to call super().trigger_delivery")
        await super().trigger_delivery(payload)

        payload_type = payload.phase
        if MessageType[payload_type] == MessageType.SEND : 
            await self.on_send(payload)
        elif MessageType[payload_type] == MessageType.ECHO : 
            await self.on_echo(payload)
        elif MessageType[payload_type] == MessageType.READY : 
            # finally, we check if the original msg is BRB delivered
            await self.on_ready(payload)

    # trigger ⟨Bracha,Deliver | s,m⟩
    def trigger_Bracha_Delivery(self, payload):

        try:
            payload_og_id = payload.u_id # original id to identify the message we want to deliver
            self.is_BRBdelivered.update({payload_og_id: True})
            self.msg_log.log(LOG_LEVEL.INFO, f"Node {self.node_id} BRB Delivered a message: {payload.u_id}.")

            self.write_metrics(payload_og_id)
            
            for u_id, status in self.is_BRBdelivered.items():
                self.msg_log.log(LOG_LEVEL.DEBUG, f"BRB Delivered Messages: Message ID: {u_id}, Delivered: {status}")

            self.msg_log.flush()

            write_to_file(self.node_id, payload.u_id)

        except Exception as e:
            self.msg_log.log(LOG_LEVEL.ERROR, f"Error in trigger_Bracha_Delivery: {e}")
            raise e
        
    """
    Malicious behavior(overload)
    """
    # u_id = hash(msg)
    # msg_id = self.generate_message_id(msg)
    # return DolevMessage(u_id, msg, msg_id, self.node_id, [], "BRACHA")
    def generate_malicious_msg(self) -> DolevMessage:
        msg = f"fake news!"
        u_id = hash(msg)
        msg_id = self.generate_message_id(msg)
        self.msg_log.log(LOG_LEVEL.INFO, f"[Malicious Node {self.node_id}] generated malicious msg to send")
    
        return DolevMessage(u_id, msg, msg_id, self.node_id, [])
    
    def mal_modify_msg(self, payload: DolevMessage) ->  DolevMessage:
        if payload:
            original_msg = payload.message
            fake_message = f"fake behaviour set on: {original_msg}"
            
            self.msg_log.log(LOG_LEVEL.INFO, f"[Malicious Node {self.node_id}] tampered the original msg")
            
            u_id = hash(fake_message)
            fake_id = self.generate_message_id(fake_message)
            return DolevMessage(u_id, fake_message, fake_id, payload.source_id, payload.path)

    def execute_mal_process(self, msg) -> DolevMessage:
        (behaviour, args) = {
            "generate_fake_msg" : (self.generate_malicious_msg, ()),
            "modify_msg_id" : (self.mal_modify_msg, (msg,)),
        }.get(self.malicious_behaviour, (None,None))
        try:
            if behaviour is None:
                raise ValueError("No valid behavior was selected for malicious processing.")
            processed_mal_msg = behaviour(*args)
        except Exception as e:
            self.msg_log.log(LOG_LEVEL.ERROR, f"Error in execute_mal_process: {e}")
            raise
        return processed_mal_msg

    """
    Optimizations
    """
    
    async def Optim1_handler(self, uuid: str, payload: DolevMessage, msg_type: MessageType):
        if self.Optim1:
            count = 0
            threshold = 0
            
            if msg_type == MessageType.ECHO:
                count = len(list(self.echo_count.get(uuid)))
                threshold = self.f + 1
                if count >= threshold and not self.check_if_echo_sent(uuid):
                    self.set_echo_sent_true(uuid)
                    await self.broadcast_message(MessageType.ECHO, payload)
                        
            elif msg_type == MessageType.READY:
                # if ():# TODO: 同时满足生成 ECHO 和 READY 消息的条件
                #     self.set_echo_sent_true(uuid)
                #     self.set_ready_sent_true(uuid)
                #     await self.broadcast_message(uuid, MessageType.READY, payload, True)
                # el
                if not self.check_if_echo_sent(uuid):
                    self.set_echo_sent_true(uuid)
                    await self.broadcast_message(MessageType.ECHO, payload)

    def is_Optim3_ECHO(self) -> bool:
        if not self.Optim3:
            return True
        if self.Optim3:
            return self.node_id <= self.Optim3_ECHO
    
    def is_Optim3_READY(self) -> bool:
        if not self.Optim3:
            return True
        if self.Optim3:
            return self.node_id <= self.Optim3_READY

    """
    Getter & Setter
    """
    def set_echo_sent_true(self, u_id, isSent = True):
        self.is_echo_sent.update({u_id: isSent})

    def set_ready_sent_true(self, u_id, isSent = True):
        self.is_ready_sent.update({u_id: isSent})

    def check_if_echo_sent(self, u_id):
        sent_echo = self.is_echo_sent.get(u_id, False)
        return sent_echo
    
    def check_if_ready_sent(self, u_id):
        return self.is_ready_sent.get(u_id, False)
                
    def increment_echo_count(self, u_id, msg_source_id):
        self.echo_count.setdefault(u_id, set()).add(msg_source_id)

    def increment_ready_count(self, u_id, msg_source_id):
        self.ready_count.setdefault(u_id, set()).add(msg_source_id)
        
    # def generate_send_msg(self, u_id, message: str, message_id: str, source_id: str, destination: List[str]): 
    #     if self.Optim2:
    #         return DolevMessage(u_id, message, self.generate_message_id(message), source_id, destination, "SEND", False)
    #     else:
    #         return DolevMessage(u_id, message, self.generate_message_id(message), source_id, destination, "SEND")
    
    # def generate_echo_msg(self, u_id, message: str, message_id: str, source_id: str, destination: List[str]):
    #     return DolevMessage(u_id,message, self.generate_message_id(message), source_id, destination, "ECHO")
    
    # def generate_ready_msg(self,u_id, message: str, message_id: str, source_id: str, destination: List[str]):
    #     return DolevMessage(u_id, message, self.generate_message_id(message), source_id, destination, "READY")
    
    
def write_to_file(id: int, uid: int):
    # for debug only
    with open('output/output.txt', 'a') as f:
        f.write(f'Node {id} delivered a message: {uid}.\n')
