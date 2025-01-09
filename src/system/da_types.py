from __future__ import annotations

import asyncio
import random
import sys
import typing
from asyncio import Event
from pathlib import Path
from threading import Lock
from typing import Dict, List, Tuple, Callable

import yaml
from ipv8.community import Community, CommunitySettings
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.interfaces.udp.endpoint import UDPv4LANAddress, UDPv4Address
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.messaging.serialization import Payload
from ipv8.types import Peer, LazyWrappedHandler, MessageHandlerFunction

from src.system.msg_history import MessageHistory

from src.implementation.node_log import message_logger, OutputMetrics, LOG_LEVEL

def sizeof(obj):
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        return size + sum(map(sizeof, obj.keys())) + sum(map(sizeof, obj.values()))
    if isinstance(obj, (list, tuple, set, frozenset)):
        return size + sum(map(sizeof, obj))
    return size


DataclassPayload = typing.TypeVar("DataclassPayload")
AnyPayload = typing.Union[Payload, DataclassPayload]


@dataclass(msg_id=0)
class ConnectionMessage:
    node_id: int
    node_state: str


def message_wrapper(*payloads: type[AnyPayload]) -> Callable[[LazyWrappedHandler], MessageHandlerFunction]:
    return lazy_wrapper(*payloads)


class DistributedAlgorithm(Community):
    # @Todo: Make sure this is configurable
    community_id = b"\x05" * 20

    _message_history: MessageHistory

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.running = False

        self._message_history = MessageHistory()
        self.algortihm_output: List[str] = []
        self.event: Event = None  # type:ignore
        # Register the message handler for messages (with the identifier "1").
        self.nodes: Dict[int, Peer] = {}
        self.node_states: Dict[int, str] = {}
        self.add_message_handler(ConnectionMessage, self._on_manual_connect)

    def node_id_from_peer(self, peer: Peer):
        try:
            key = next((key for key, p in self.nodes.items() if p == peer))
            assert key is not None
        except Exception as e:
            print(f"Error in node_id_from_peer: {e}")
            raise e

        return next((key for key, p in self.nodes.items() if p == peer), None)

    async def started(
            self,
            node_id: int,
            connections: List[Tuple[int, int]],
            event: Event,
            use_localhost: bool = True,
            starting_node=0,
            output_file: str = "output/node.out",
            stat_file: str = "output/node.yml",
    ) -> None:
        self.event = event
        self.node_id = node_id
        self.starting_node = starting_node
        self.algortihm_output_file = Path(output_file)
        self.algortihm_output_file = (
                self.algortihm_output_file.parent
                / f"{self.algortihm_output_file.stem}-{node_id}{self.algortihm_output_file.suffix}"
        )

        self.msg_level = LOG_LEVEL.INFO
        self.msg_log = message_logger(self.node_id,self.algortihm_output_file,OutputMetrics(),self.msg_level) #default constructor to make python happy

        self.stat_file = Path(stat_file)
        self.stat_file = self.stat_file.parent / f"{self.stat_file.stem}-{node_id}{self.stat_file.suffix}"
        connections = list(set(connections))
        self.connections = connections
        self.connectionLock = Lock()
        self.on_start_delay = random.uniform(2.0, 3.0)  # Seconds
        host_network = self._get_lan_address()[0]
        host_network_base = ".".join(host_network.split(".")[:3])
        print(f"[Node {self.node_id}] booting on {host_network_base}.{self.node_id + 10}")

        async def _ensure_nodes_connected() -> None:
            try:
                for node_id, conn in self.connections:
                    ip_address = f"{host_network_base}.{node_id + 10}"
                    self.node_states[node_id] = "init"
                    if use_localhost:
                        ip_address = host_network
                    ad = (ip_address, conn)
                    self.walk_to(ad)
                valid = False
                conn_nodes = []

                await asyncio.sleep(1)
                with self.connectionLock:
                    if len(self.get_peers()) == len(self.connections):
                        valid = True
                if not valid:
                    return

                for peer in self.get_peers():
                    conn_msg = ConnectionMessage(self.node_id, "init")
                    self.ez_send(peer, conn_msg)

                valid = False
                with self.connectionLock:
                    if len(self.nodes) == len(self.connections):
                        valid = True
                if not valid:
                    return

                self.cancel_pending_task("ensure_nodes_connected")
                self.register_anonymous_task("delayed_start", self.on_start, delay=self.on_start_delay)
            except Exception as e:
                print(f"[Node {self.node_id}] Error in ensure_nodes_connected: {e}")
                # raise e

        self.register_task("ensure_nodes_connected", _ensure_nodes_connected, interval=0.5, delay=1)

    async def on_start(self):
        # print(f"[Node {self.node_id}] Starting algorithm with peers {[x.address for x in self.get_peers()]} and {self.nodes}")
        if self.node_id == self.starting_node:
            # Checking if all node states are ready
            all_ready = all([x == "ready" for x in self.node_states.values()])
            while not all_ready:
                await asyncio.sleep(1)
                all_ready = all([x == "ready" for x in self.node_states.values()])
            await asyncio.sleep(1)
            await self.on_start_as_starter()

        print(f"[Node {self.node_id}] is ready")
        for peer in self.get_peers():
            self.ez_send(peer, ConnectionMessage(self.node_id, "ready"))

    @message_wrapper(ConnectionMessage)
    def _on_manual_connect(self, peer: Peer, payload: ConnectionMessage):
        # print(f"[Node {self.node_id}] Got connection message from {payload.node_id} with state {payload.node_state} len(self.nodes)={len(self.nodes)} =?= {len(self.connections)}")
        self.nodes[payload.node_id] = peer
        peer_port = peer.address[1]
        self.node_states[payload.node_id] = payload.node_state
        self.nodes[payload.node_id] = peer

    async def on_start_as_starter(self):
        pass

    def stop(self, delay: int = 0):

        async def delayed_stop():
            print(f"[Node {self.node_id}] Stopping algorithm")
            self.save_algorithm_output()
            self.save_node_stats()
            self.event.set()

        self.register_anonymous_task("delayed_stop", delayed_stop, delay=delay)

    def ez_send(self, peer: Peer, *payloads: AnyPayload, **kwargs) -> None:
        addr = peer.addresses.get(UDPv4LANAddress, None)
        if addr is None:
            addr = peer.addresses.get(UDPv4Address, None)
        assert addr is not None
        self._message_history.add_message(*payloads, destination=addr)
        self._ez_senda(addr, *payloads, **kwargs)

    def add_message_handler(self, msg_num: int | type[AnyPayload], callback: MessageHandlerFunction) -> None:
        super().add_message_handler(msg_num, callback)

    def on_packet(self, packet: Tuple[Tuple[str | int] | bytes], warn_unknown: bool = True) -> None:
        # import time
        # time.sleep(3)
        return super().on_packet(packet, warn_unknown)

    def append_output(self, line: str):
        self.algortihm_output.append(line)

    def save_algorithm_output(self):
        p = Path(self.algortihm_output_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Write all the output lines to the file f
        with open(p, "w") as f:
            for line in self.algortihm_output:
                f.write(line + "\n")
        print(f"[Node {self.node_id}] Algorithm output saved to {p} in {p.resolve()}")

    def save_node_stats(self):
        p = Path(self.stat_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        stats = {"messages_received": len(self._message_history), "bytes_sent": self._message_history.bytes_sent()}
        # Save stats object as yaml
        with open(p, "w") as f:
            yaml.dump(stats, f)

        print(f"[Node {self.node_id}] Node stats saved to {p} in {p.resolve()}")
