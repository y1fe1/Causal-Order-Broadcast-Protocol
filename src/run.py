import argparse
import os
import sys
import yaml
from asyncio import run
from ipv8.configuration import ConfigBuilder, default_bootstrap_defs
from ipv8.util import create_event_with_signals
from ipv8_service import IPv8
# from ipv8.community import Community
from algorithms import *


def get_algorithm(name: str) -> DistributedAlgorithm:
    algorithms = {
        'echo': EchoAlgorithm,
        'election': RingElection,
    }
    if name not in algorithms.keys():
        raise Exception(f'Cannot find select algorithm with name {name}')
    return algorithms[name]

async def start_communities(node_id, connections, algorithm, use_localhost = True) -> None:
    event = create_event_with_signals()
    base_port = 9090
    connections_updated = [(x, base_port + x) for x in connections]
    node_port = base_port + node_id
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec{node_id}.pem")
    builder.set_port(node_port)
    builder.add_overlay(
        "DA_Alg_Test",
        "my peer",
        [],
        default_bootstrap_defs,
        {},
        [("started", node_id, connections_updated, event, use_localhost)],
    )
    ipv8_instance = IPv8(
        builder.finalize(), extra_communities={"DA_Alg_Test": algorithm}
    )
    await ipv8_instance.start()
    await event.wait()
    await ipv8_instance.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Distributed Algorithms",
        description="Code to execute distributed algorithms.",
        epilog="written by Bart Cox (2023)",
    )
    parser.add_argument("node_id", type=int)
    parser.add_argument("topology", type=str, nargs="?", default="topologies/default.yaml")
    parser.add_argument("algorithm", type=str, nargs="?", default='echo')
    parser.add_argument("-docker", action='store_true')
    args = parser.parse_args()
    node_id = args.node_id

    alg = get_algorithm(args.algorithm)
    with open(args.topology, "r") as f:
        topology = yaml.safe_load(f)
        connections = topology[node_id]

        run(start_communities(node_id, connections, alg, not args.docker))
