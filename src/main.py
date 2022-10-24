import asyncio
import sys
from pathlib import Path
from typing import Union

from echoprocess import EchoProcess


def load_addresses(path: Union[str, Path]) -> dict:
    """
    Util function to load addresses from file into a dictionary object
    :param path:
    :return: dictionary containing tuples (host, port) of all processes. Keys are the ids of the processes.
    """
    addresses = {}
    # Good practice to work with path objects
    path = Path(path)
    f = open(path, 'r')
    for line in f:
        # We expect a triple seperated by spaces
        pid, host, port = line.rstrip().split(' ')
        addresses[int(pid)] = (host, int(port))
    return addresses


async def run_process(pid: int):
    """
    Util function to run the process asynchronous
    :param pid: pid of own process
    :return: void
    """
    # Load addresses of all processes in the system
    addresses = load_addresses('resources/addresses.txt')
    # Start own process
    p = EchoProcess(pid, addresses)
    # Start server for incomming connections
    await p.start_server()
    # Wait a bit for all processes to start up
    await asyncio.sleep(1)
    # Run algorithm until finished
    await p.run()


if __name__ == '__main__':
    # Parse pid from CLI
    p_id = int(sys.argv[1])
    asyncio.run(run_process(p_id))
