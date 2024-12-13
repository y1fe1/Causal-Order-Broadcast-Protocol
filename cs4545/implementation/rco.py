import random
import datetime

from ipv8.community import CommunitySettings

from cs4545.implementation.dolev_rc_new import DolevMessage, MessageType
from cs4545.implementation.node_log import LOG_LEVEL
from cs4545.implementation.bracha_rb import BrachaRB, BrachaConfig

class RCOConfig(BrachaConfig):
    def __init__(self, broadcasters={1:1}, malicious_nodes=[], N=10, msg_level=LOG_LEVEL.DEBUG):
        super().__init__(broadcasters, malicious_nodes, N, msg_level)

class RCO(BrachaRB):
    def __init__(self, settings: CommunitySettings, parameters=RCOConfig()):
        super().__init__(settings, parameters)
        self.vector_clock = [0 for _ in range(self.N)]
        self.pending = []

    async def on_start(self):
        await super().on_start()

    async def on_start_as_starter(self):
        await super().on_start_as_starter()

    def compare_vector_lock(self, new_VC) -> bool:
        self.msg_log.log(LOG_LEVEL.DEBUG, f"Comparing Vectors: {self.vector_clock} >= {new_VC} ?")
        return all([self.vector_clock[i] >= new_VC[i] for i in range(self.N)])

    def generate_message(self) -> DolevMessage:
        msg = f"msg_{self.message_broadcast_cnt+1}th_" + \
        "".join([random.choice(['TUD', 'NUQ', 'LOO', 'THU']) for _ in range(6)])
        u_id = self.get_uid_pred()
        msg_id = self.generate_message_id(msg)    # 调用父类实现
        return DolevMessage(u_id, msg, msg_id, self.node_id, [],
                            self.vector_clock, MessageType.BRACHA.value)

    async def on_broadcast(self, message: DolevMessage):
        """ upon event < RCO, Broadcast | M > do """

        self.msg_log.log(LOG_LEVEL.DEBUG, f"Node {self.node_id} is RCO broadcasting: {message.message}")

        self.trigger_RCO_delivery(message)
        await super().on_broadcast(message)
        self.vector_clock[self.node_id] += 1

    def trigger_Bracha_Delivery(self, payload):
        """ upon event < RB, Deliver | M > do """

        self.msg_log.log(LOG_LEVEL.DEBUG, f"Node {self.node_id} is Trying to trigger BRB Delivery: {payload.message}")

        super().trigger_Bracha_Delivery(payload)
        src = payload.source_id

        self.msg_log.log(LOG_LEVEL.DEBUG, f"The message from: {src}")

        if True: #src != self.node_id: <- TODO: should be this, but why is source_id changed halfway?
            self.pending.append((src, payload))

            self.msg_log.log(LOG_LEVEL.DEBUG, f"My pending: {self.pending}")

            self.deliver_pending()

    def deliver_pending(self):
        """ procedure deliver pending """

        self.msg_log.log(LOG_LEVEL.DEBUG, f"Node {self.node_id} is entering deliver_pending")
        to_keep = []
        for src, msg in self.pending:
            if self.compare_vector_lock(msg.vector_clock):
                self.trigger_RCO_delivery(msg)
                self.vector_clock[src] += 1
            else:
                to_keep.append((src, msg))
        self.pending = to_keep
        
    def trigger_RCO_delivery(self, payload):
        """ upon event < RCO, Deliver | M > do """

        delivered_time = datetime.datetime.now()
        self.msg_log.log(LOG_LEVEL.INFO, f"Node {self.node_id} RCO Delivered a message:<{payload.message}>. Time: {delivered_time}")

