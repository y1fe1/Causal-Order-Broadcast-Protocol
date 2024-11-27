from .echo_algorithm import *
from .ring_election import *
from .dolev_rc import *


def get_algorithm(name):
    if name == "echo":
        return EchoAlgorithm
    elif name == "ring":
        return RingElection
    elif name == "dolev":
        return BasicDolevRC
    else:
        raise ValueError(f"Unknown algorithm: {name}")
