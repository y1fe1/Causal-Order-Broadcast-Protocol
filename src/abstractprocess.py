from __future__ import annotations

import asyncio
import pickle
import queue
import random
from abc import ABC, abstractmethod


class Message:
    """
    Implementation of a message object.
    This can be changed by the student
    """
    sender = 0
    content = ''

    def __init__(self, content, sender):
        self.sender = sender
        self.content = content

    def encode(self) -> bytes:
        """
        Make sure we are serializable with EOF line ending
        :return: Bytestring of the object
        """
        return pickle.dumps(self) + '\n'.encode()

    @classmethod
    def decode(cls, bytestring) -> Message:
        """
        Make sure we can decode messages
        :param bytestring: bytestring of the Message object
        :return: Message object
        """
        return pickle.loads(bytestring)


class MessageBuffer:
    """
    Queue objects to keep track of all the incoming messages.
    Acts as an inbox following the actor model.
    NOTE: No checks are done to prevent exceptions.
    """
    messages = None

    def __init__(self):
        self.messages = queue.Queue()

    def size(self) -> int:
        return self.messages.qsize()

    def has_messages(self) -> bool:
        return self.size() > 0

    def put(self, m: Message):
        self.messages.put(m)

    def get(self):
        return self.messages.get()


class AbstractProcess(ABC):
    server = None
    running = True
    host = ''
    port = 0
    buffer = None
    # Variables to control the random delay each process has while executing the algorithm
    # Set both to 0 to remove any delays
    delay_min = 0
    delay_max = 1

    def __init__(self, idx: int, addresses):
        self.idx = idx
        self.addresses: dict = addresses
        self.host, self.port = self.addresses.pop(self.idx)
        self.buffer = MessageBuffer()

    @abstractmethod
    async def algorithm(self):
        """
        Needs to be implemented.
        See EchoProcess as an example.
        :return:
        """
        pass

    async def _random_delay(self, min_time: int = None, max_time: int = None):
        """
        Delays the execution for a random time N such that a <= N <= b for a <= b and b <= N <= a for b < a.
        :param min_time: minimum delay in seconds
        :param max_time: maximin delay in seconds
        :return:
        """
        if not min_time or not max_time:
            min_time = self.delay_min
            max_time = self.delay_max
        delay_time = random.uniform(min_time, max_time)
        await asyncio.sleep(delay_time)

    async def send_message(self, m: Message, to: int):
        """
        Send a message asynchronous to another process.
        :param m: Message object
        :param to: pid of the other process as mapped in the addresses' dictionary
        :return:
        """
        # Retrieve address from address dictionary
        host, port = self.addresses[to]
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(m.encode())
        await writer.drain()
        writer.close()

    async def _handle_message(self, reader, writer):
        """
        Accepts incoming messages and stores them in the message buffer.
        writer.get_extra_info('peername') can be used to retrieve more information about the sender if desired.
        :param reader: StreamReader object
        :param writer: StreamWriter object
        :return:
        """
        # Read data as bytestring
        data = await reader.readline()
        # Decode into Message object
        message = Message.decode(data)
        # Store message in message buffer to be handled by the algorithm() function
        self.buffer.put(message)
        writer.close()

    async def start_server(self):
        # Create socket server for incoming connections
        self.server = await asyncio.start_server(self._handle_message, self.host, self.port)
        # Start listening
        await self.server.start_serving()
        print(f'Serving on {", ".join(str(sock.getsockname()) for sock in self.server.sockets)}')

    async def run(self):
        """
        Run the main loop of the process.
        Listen both to the incoming messages and call the algorithm() function
        :return:
        """
        async with self.server:
            while self.running:
                await self.algorithm()
                await self._random_delay()
            print('Stopping server')
            # Wait a bit for a more graceful exit of all the nodes
            await asyncio.sleep(2)
            # Stop server
            self.server.close()
            print('Exiting')
