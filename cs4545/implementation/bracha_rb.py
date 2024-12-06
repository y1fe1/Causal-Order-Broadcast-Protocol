import datetime
import logging
import random
import math


from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from cs4545.system.da_types import DistributedAlgorithm, message_wrapper
from hashlib import sha256

from cs4545.implementation.node_log import message_logger, OutputMetrics

class BrachaConfig:
    def __init__(self, broadcasters = {1:2, 2:1}, malicious_nodes = [3], f = 2, N = 10, msg_level = logging.DEBUG):
        self.broadcasters = broadcasters            # broadcaster_id -> repeated_times
        self.malicious_nodes = malicious_nodes
        self.f = f
        self.N = N

        self.msg_level = msg_level


class BrachaMessage:
    message: str
    message_id: str

@dataclass(
    msg_id=3
) 
class SendMessage(BrachaMessage):
    pass

@dataclass(
    msg_id=4
) 
class EchoMessage(BrachaMessage):
    pass

@dataclass(
    msg_id=5
) 
class ReadyMessage(BrachaMessage):
    pass

class BrachaRB(DistributedAlgorithm):
    def __init__(self, settings: CommunitySettings, parameters = BrachaConfig()) -> None:
        super().__init__(settings)

        self.f = parameters.f
        self.N = parameters.N

        self.connectivity = len(self.get_peers())

        self.broadcasters = parameters.broadcasters
        self.malicious_nodes = parameters.malicious_nodes
        
        self.echo_count:    dict[str, int]  = {}   # message_id -> echo count
        self.ready_count:   dict[str, int]  = {}   # message_id -> ready count

        self.is_ready_sent: dict[str, bool] = {}   # message_id -> is READY message sent
        self.is_delivered:  dict[str, bool] = {}   # message_id -> is Delivered

        self.add_message_handler(SendMessage, self.on_send)
        self.add_message_handler(EchoMessage, self.on_echo)
        self.add_message_handler(ReadyMessage, self.on_ready)

        node_outputMetrics = OutputMetrics(self)
        self.algortihm_output_file = self.gen_output_file_path()

        self.msg_log = message_logger(self.node_id,parameters.msg_level, self.algortihm_output_file,node_outputMetrics)

    def gen_output_file_path(self, test_name: str ="Bracha_Test") : 

        '''
            To be fair this should be part of the parent class function to Insert
            This function will set the output file to be output/{test_name}_{time_stamp}/node-{node_id}.out
        '''

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subdirectory_name = f"{test_name}_{timestamp}"

        return (self.algorithm_output_file.parent 
                                      / subdirectory_name
                                      / self.algortihm_output_file.name)

    def generate_message(self) -> SendMessage:
        msg =  ''.join([random.choice(['uk', 'pk', 'mkk', 'fk']) for _ in range(6)])
        id = sha256(msg.encode()).hexdigest()
        return SendMessage(msg, id)
    
    async def on_start(self):
       
        self.msg_log.log("INFO",  f'Node {self.node_id} is starting.')

        if self.node_id in self.broadcasters.keys():
            for _ in range(self.broadcasters[self.node_id]):
                await self.on_broadcast()

    async def on_broadcast(self) -> None:
        
        self.msg_log.log("INFO",f'Node {self.node_id} is broadcasting.')
        
        message = self.generate_message()

        for peer in self.get_peers():
            self.ez_send(peer, message)

    @message_wrapper(SendMessage)
    async def on_send(self, peer: Peer, payload: SendMessage):
        
        self.msg_log.log("DEBUG", f'Received a SEND  message: {payload.message_id}.')

        for p in self.get_peers():
            self.ez_send(p, EchoMessage(payload.message, payload.message_id))

    @message_wrapper(EchoMessage)
    async def on_echo(self, peer: Peer, payload: EchoMessage):
        
        self.msg_log.log("DEBUG", f'Received an ECHO message: {payload.message_id}.')
        
        self.echo_count.setdefault(payload.message_id, 0)
        self.echo_count[payload.message_id] += 1
        
        if not self.is_ready_sent.get(payload.message_id) and \
            self.echo_count[payload.message_id] >= math.ceil((self.f + self.N + 1) / 2):
            self.is_ready_sent.setdefault(payload.message_id, True)
            
            
            self.msg_log.log("DEBUG",f'Sent READY messages: {payload.message_id}')

            for p in self.get_peers():
                self.ez_send(p, ReadyMessage(payload.message, payload.message_id))
            
    @message_wrapper(ReadyMessage)
    async def on_ready(self, peer: Peer, payload: ReadyMessage):

        self.msg_log.log("DEBUG", f'Received a READY message: {payload.message_id}.')

        if not self.is_ready_sent.get(payload.message_id):

            self.ready_count.setdefault(payload.message_id, 0)
            self.ready_count[payload.message_id] += 1

            if self.ready_count[payload.message_id] >= self.f + 1:
                self.is_ready_sent.setdefault(payload.message_id, True)

                self.msg_log.log("DEBUG",f'Sent READY messages: {payload.message_id}')

                for p in self.get_peers():
                    self.ez_send(p, ReadyMessage(payload.message, payload.message_id))

        self.ready_count.setdefault(payload.message_id, 0)
        self.ready_count[payload.message_id] += 1

        if not self.is_delivered.get(payload.message_id) and \
            self.ready_count.get(payload.message_id) >= 2 * self.f + 1:
            self.is_delivered.setdefault(payload.message_id, True)

            self.trigger_delivery(payload)

    def trigger_delivery(self, payload: BrachaMessage):

        self.msg_log.log("DEBUG",f'Delivered a message: {payload.message_id}.')

        



        
        