from typing import List
from src.system.da_types import *


@dataclass(msg_id=3)  # The value 1 identifies this message and must be unique per community.
class MyMessage:
    counter: int
    randomList: List[int]


class EchoAlgorithm(DistributedAlgorithm):
    """_summary_
    Simple example that just echoes messages between two nodes
    Args:
        DistributedAlgorithm (_type_): _description_
    """

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.echo_counter = 0
        self.max_echo_count = 10
        self.add_message_handler(MyMessage, self.on_message)

    async def on_start(self):
        # Make sure to call this one last in this function
        await super().on_start()

    async def on_start_as_starter(self):
        print(f"Node {self.node_id} is starting the algorithm")
        peer = self.get_peers()[0]
        random_list = [random.randint(0, 65535) for _ in range(self.max_echo_count)]
        self.ez_send(peer, MyMessage(self.echo_counter, random_list))

    @message_wrapper(MyMessage)
    async def on_message(self, peer: Peer, payload: MyMessage) -> None:
        try:
            sender_id = self.node_id_from_peer(peer)
            self.append_output(f"{sender_id}-{self.echo_counter}")
            self.echo_counter = payload.counter + 1
            if self.echo_counter >= self.max_echo_count:
                print(f"Node {self.node_id} is stopping")
                self.stop()
            print(
                f"[Node {self.node_id}] Got a message from node: {sender_id}.\t current counter: {self.echo_counter} and random list: {payload.randomList}")
            # Then synchronize with the rest of the network again.
            random_list = [random.randint(0, 65535) for _ in range(self.max_echo_count)]
            self.ez_send(peer, MyMessage(self.echo_counter, random_list))
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e
