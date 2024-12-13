from .echo_algorithm import *
from .ring_election import *
from .dolev_rc_new import *
from .bracha_rb import *
from .rco import *

def get_algorithm(name):
    if name == "echo":
        return EchoAlgorithm
    elif name == "ring":
        return RingElection
    elif name == "dolev":
        return BasicDolevRC
    elif name == "bracha":
        return BrachaRB
    elif name == "RCO" or name == "rco":
        return RCO
    else:
        raise ValueError(f"Unknown algorithm: {name}")
