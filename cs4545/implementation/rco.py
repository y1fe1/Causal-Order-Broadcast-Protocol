import random
import datetime
import asyncio

from ipv8.community import CommunitySettings

from cs4545.implementation.dolev_rc_new import DolevMessage, MessageType
from cs4545.implementation.node_log import LOG_LEVEL
from cs4545.implementation.bracha_rb import BrachaRB, BrachaConfig

class RCOConfig(BrachaConfig):
    def __init__(self, broadcasters={0:1}, malicious_nodes=[], N=10, msg_level=LOG_LEVEL.WARNING, causal_broadcast = [8,9,6,4]):
        """
        Previously, we use broadcasters = {1:2, 2:1, ...} to launch concurrent broadcasts.
        From now on, the messages should be made causally related.
        The way we do this is to have the message specify its successor(s), i.e. the next node to broadcast.
        eg. If a message is "#msg_content#4698" sent by 1, then broadcasts will go as 1->8->9->6->4->end 
        """
        super().__init__(broadcasters, malicious_nodes, N, msg_level)
        self.causal_broadcast = causal_broadcast

class RCO(BrachaRB):
    def __init__(self, settings: CommunitySettings, parameters=RCOConfig()):
        super().__init__(settings, parameters)
        self.causal_broadcast = parameters.causal_broadcast
        self.vector_clock = [0 for _ in range(self.N)]
        self.pending = []

    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        await super().on_start_as_starter()

    def compare_vector_lock(self, new_VC) -> bool:
        self.msg_log.log(self.msg_level, f"Comparing Vectors: {self.vector_clock} >= {new_VC} ?")
        return all([self.vector_clock[i] >= new_VC[i] for i in range(self.N)])

    def generate_message(self, suffix="None") -> DolevMessage:
        msg = f"msg_{self.message_broadcast_cnt+1}th_" + \
        "".join([random.choice(['TUD', 'NUQ', 'LOO', 'THU']) for _ in range(6)])

        if suffix == "None":
            suffix = "".join([str(id) for id in self.causal_broadcast])
            suffix = suffix[::-1]
        msg = msg + "_" + suffix

        u_id = self.get_uid_pred()
        msg_id = self.generate_message_id(msg)
        author_id = self.node_id
        return DolevMessage(u_id, msg, msg_id, self.node_id, [],
                            self.vector_clock, MessageType.BRACHA.value, True, author_id)

    async def on_broadcast(self, message: DolevMessage):
        """ upon event < RCO, Broadcast | M > do """

        self.msg_log.log(self.msg_level, f"Node {self.node_id} is RCO broadcasting: {message.message}")

        self.trigger_RCO_delivery(message)
        await super().on_broadcast(message)
        self.vector_clock[self.node_id] += 1

    def trigger_Bracha_Delivery(self, payload):
        """ upon event < RB, Deliver | M > do """

        super().trigger_Bracha_Delivery(payload)
        author = payload.author_id

        self.msg_log.log(self.msg_level, f"Node {self.node_id} BRB Delivered: {payload.message} from {author}")

        if author != self.node_id: 
            self.pending.append((author, payload))

            self.msg_log.log(self.msg_level, f"My pending: {self.pending}")

            self.deliver_pending()

    def deliver_pending(self):
        """ procedure deliver pending """

        self.msg_log.log(self.msg_level, f"Node {self.node_id} is entering deliver_pending")

        to_keep = []
        while True:
            flag = False
            for author, msg in self.pending:
                if self.compare_vector_lock(msg.vector_clock):
                    self.trigger_RCO_delivery(msg)
                    self.vector_clock[author] += 1
                    flag = True
                else:
                    to_keep.append((author, msg))
            self.pending = to_keep
            if not flag:
                break
    
    def get_next_broadcast(self, payload: DolevMessage):
        """ get the next broadcaster and the next message suffix"""
        msg = payload.message
        next_id, suffix = -1, ""
        if msg[-1].isdigit():
            next_id = int(msg[-1])
            suffix = msg.split('_')[-1]
            suffix = suffix[:-1]
        return next_id, suffix
        
    def trigger_RCO_delivery(self, payload: DolevMessage):
        """ upon event < RCO, Deliver | M > do """

        delivered_time = datetime.datetime.now()
        author = payload.author_id
        self.msg_log.log(self.msg_level, f"Node {self.node_id} RCO Delivered a message:<{payload.message}>. Time: {delivered_time}. Author: {author}.")

        next_id, suffix = self.get_next_broadcast(payload)
        if next_id == self.node_id:
            new_payload = self.generate_message(suffix=suffix)
            self.msg_log.log(self.msg_level, f"Node {self.node_id} is the next broadcaster for message: <{new_payload.message}>. Current message: <{payload.message}>")
            asyncio.create_task(self.on_broadcast(new_payload))