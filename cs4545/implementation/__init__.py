from .echo_algorithm import *
from .ring_election import *


def get_algorithm(name):
    if name == "echo":
        return EchoAlgorithm
    elif name == "ring":
        return RingElection
    else:
        raise ValueError(f"Unknown algorithm: {name}")
