from abstractprocess import AbstractProcess, Message


class EchoProcess(AbstractProcess):
    """
    Example implementation of a distributed process.
    This example sends and echo's 10 messages to another process.
    Only the algorithm() function needs to be implemented.
    The function send_message(message, to) can be used to send asynchronous messages to other processes.
    The variables first_cycle and num_echo are examples of variables custom to the EchoProcess algorithm.
    """
    first_cycle = True
    num_echo = 15
    counter = 1

    async def algorithm(self):
        # Only run in the beginning
        if self.first_cycle:
            # Compose message
            msg = Message("Hello world", self.idx, self.counter)
            # Get first address we can find
            to = list(self.addresses.keys())[0]
            # Send message
            await self.send_message(msg, to)
            self.first_cycle = False

        # If we have a new message
        if self.buffer.has_messages():
            # Retrieve message
            msg: Message = self.buffer.get()
            print(f'[{self.num_echo}] Got message "{msg.content}" from process {msg.sender}, counter: {msg.counter}')
            # Compose echo message
            echo_msg = Message(msg.content, self.idx, self.counter)
            self.counter += 1
            # Send echo message
            await self.send_message(echo_msg, msg.sender)
            self.num_echo -= 1
            if self.num_echo == 0:
                print('Exiting algorithm')
                self.running = False
