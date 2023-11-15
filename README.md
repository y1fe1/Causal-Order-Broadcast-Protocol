# Python Template

This code is offered as a template for the course IN4150.
This template is tested on Ubuntu 20.04 (should also work on Windows and Mac OSX).
NOTE: When running locally Python >= 3.8  is required.

## Docs

- IPv8 ([ipv8-docs](https://py-ipv8.readthedocs.io/en/latest/index.html)).
- Asyncio ([docs](https://docs.python.org/3/library/asyncio.html)) is heavily used for the implementation of this code.

## File structure

- **src:** Holds all the python source files
- **src/algorithms:** Contains code for different distributed algorithms
- **topologies/default.yaml:** List of the addresses of all the processes that are participating in the algorithm.
- **Dockerfile:** Dockerfile describing the image that is used by docker-compose
- **docker-compose.yml:** Yaml file that describes the system for docker-compose.
- **docker-compose.template.yml:** Yaml file used as a template for the `src/util.py` script.
- **run_echo.sh:** Script to run the echo example.
- **run_election.sh:** Script to run the ring election example.

## Topology File
The topology file (in `./topologies`) is used to define how the nodes in the system are connected.
The yaml file is a list of node ids with the corresponding connections to other nodes.
To increase the number of nodes in a topology, run the `util.py` script.
By default, `util.py` creates a ring topology. If you want/need to use another topology (fully-connected, parse network, ...), adjust the script.

## Remarks

1. Feel free to change any of the files. This template is offered as starting point with working messaging between distributed processes.
2. Be sure to adjust the topology based on the assignment. By default, `util.py` creates a ring topology. If you want/need to use another topology (fully-connected, parse network, ...), adjust the script.


## Prerequisites

- Docker
- Docker-compose
- (Python >= 3.8 if running locally)

Install dependencies:

```bash
pip install -r requirements.txt
```

Expected output is the same as when running with docker-compose.

## Examples Docker

### Echo algorithm

```bash
NUM_NODES=2
python src/util.py $NUM_NODES topologies/echo.yaml echo
docker compose build
docker compose up
```

Expected output:

```text
in4150-python-template-node1-1  | [Node 1] Starting
in4150-python-template-node0-1  | [Node 0] Starting
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 1
in4150-python-template-node1-1  | [Node 1] Got a message from node: 0.   current counter: 2
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 3
in4150-python-template-node1-1  | [Node 1] Got a message from node: 0.   current counter: 4
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 5
in4150-python-template-node1-1  | [Node 1] Got a message from node: 0.   current counter: 6
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 7
in4150-python-template-node1-1  | [Node 1] Got a message from node: 0.   current counter: 8
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 9
in4150-python-template-node1-1  | Node 1 is stopping
in4150-python-template-node1-1  | [Node 1] Got a message from node: 0.   current counter: 10
in4150-python-template-node1-1  | [Node 1] Stopping algorithm
in4150-python-template-node0-1  | Node 0 is stopping
in4150-python-template-node0-1  | [Node 0] Got a message from node: 1.   current counter: 11
in4150-python-template-node0-1  | [Node 0] Stopping algorithm
in4150-python-template-node1-1 exited with code 0
in4150-python-template-node0-1 exited with code 0
```

### Ring Election algorithm

```bash
NUM_NODES=4
python src/util.py $NUM_NODES topologies/election.yaml election
docker compose build
docker compose up
```

Expected output:

```text
in4150-python-template-node2-1  | [Node 2] Starting
in4150-python-template-node0-1  | [Node 0] Starting
in4150-python-template-node3-1  | [Node 3] Starting
in4150-python-template-node1-1  | [Node 1] Starting
in4150-python-template-node3-1  | [Node 3] Starting by selecting a node: 0
in4150-python-template-node0-1  | [Node 0] Got a message from with elector id: 3
in4150-python-template-node1-1  | [Node 1] Got a message from with elector id: 3
in4150-python-template-node2-1  | [Node 2] Got a message from with elector id: 3
in4150-python-template-node3-1  | [Node 3] Got a message from with elector id: 3
in4150-python-template-node3-1  | [Node 3] we are elected!
in4150-python-template-node3-1  | [Node 3] Sending message to terminate the algorithm!
in4150-python-template-node0-1  | [Node 0] Stopping algorithm
in4150-python-template-node1-1  | [Node 1] Stopping algorithm
in4150-python-template-node2-1  | [Node 2] Stopping algorithm
in4150-python-template-node3-1  | [Node 3] Stopping algorithm
```

## Examples local

Expected output is the same as when running with docker-compose.

### Echo algorithm

```bash
python src/run.py 0 topologies/echo.yaml echo &
python src/run.py 1 topologies/echo.yaml echo &
```

### Ring Election algorithm

```bash
python src/run.py 0 topologies/election.yaml election &
python src/run.py 1 topologies/election.yaml election &
python src/run.py 2 topologies/election.yaml election &
python src/run.py 3 topologies/election.yaml election &
```
