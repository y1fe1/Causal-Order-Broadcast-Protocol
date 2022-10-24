# Python Template
This code is offered as a template for the course IN4150.
This template is tested on Ubuntu 20.04 (should also work on Windows and Mac OSX).
NOTE: When running locally Python >= 3.8  is required.
Asyncio ([docs](https://docs.python.org/3/library/asyncio.html)) is heavily used for the implementation of this templates.

## File structure
- **src:** Holds all the python source files
- **resources/addresses.txt:** List of the addresses of all the processes that are participating in the algorithm.
- **resources/addresses_docker.txt:** Same but then for the docker implementation because the hostnames are different.
- **Dockerfile:** Dockerfile describing the image that is used by docker-compose
- **docker-compose.yml:** Yaml file that describes the system for docker-compose.

## Remarks
1. Feel free to change any of the files. This template is offered as starting point with working messaging between distributed processes.
2. `addresses_docker.txt` is loading into the docker image as `addresses.txt`. You don't have to change the source code when switching from running locally for debugging to running with docker-compose.
3. Both `addresses.txt` and `addresses_docker.txt` follow the structure of `<processId> <hostname/ip/> <port>` for each line.
## Prerequisites
* Docker
* Docker-compose
* (Python >= 3.8 if running locally)

## Run via docker-compose
```bash
docker-compose build
docker-compose up
```

Expected output:
```text
Attaching to in4150-python-template_node0_1, in4150-python-template_node1_1
node1_1  | Serving on ('172.22.0.3', 9091)
node0_1  | Serving on ('172.22.0.2', 9090)
node1_1  | [10] Got message "Hello world" from process 0
node0_1  | [10] Got message "Hello world" from process 1
node0_1  | [9] Got message "Hello world" from process 1
node1_1  | [9] Got message "Hello world" from process 0
node0_1  | [8] Got message "Hello world" from process 1
node1_1  | [8] Got message "Hello world" from process 0
node0_1  | [7] Got message "Hello world" from process 1
node1_1  | [7] Got message "Hello world" from process 0
node0_1  | [6] Got message "Hello world" from process 1
node1_1  | [6] Got message "Hello world" from process 0
node0_1  | [5] Got message "Hello world" from process 1
node1_1  | [5] Got message "Hello world" from process 0
node0_1  | [4] Got message "Hello world" from process 1
node1_1  | [4] Got message "Hello world" from process 0
node1_1  | [3] Got message "Hello world" from process 0
node0_1  | [3] Got message "Hello world" from process 1
node0_1  | [2] Got message "Hello world" from process 1
node1_1  | [2] Got message "Hello world" from process 0
node1_1  | [1] Got message "Hello world" from process 0
node1_1  | Exiting algorithm
node0_1  | [1] Got message "Hello world" from process 1
node0_1  | Exiting algorithm
node1_1  | Stopping server
node0_1  | Stopping server
node1_1  | Exiting
in4150-python-template_node1_1 exited with code 0
node0_1  | Exiting
in4150-python-template_node0_1 exited with code 0
```

## Run locally (for debugging)
```bash
python3.8 -u src/main.py 0 &
python3.8 -u src/main.py 1 &
# As many commands as there are nodes in your algorithm/implementation
python3.8 -u src/main.py n &
```

Expected output is the same as when running with docker-compose.
