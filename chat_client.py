import asyncio
import argparse
import socket
import json


class ChatClient(asyncio.Protocol):

    def data_received(self, data):
        self.data += data
        if self.data.endswith(b'\0'):
            answer = get_answer(self.data)
            self.transport.write(answer)
            self.data = b''


@asyncio.coroutine
def handle_user_input(loop):
    ip = socket.gethostbyname(socket.gethostname())

    while True:
        message = yield from loop.run_in_excutor(None, input, "> ")
        if message == "quit":
            loop.stop()
            return
        print(message)


def run_client(host, port):
    loop = asyncio.get_event_loop()
    client = ChatClient()
    coro = loop.create_connection(lambda: client, host, port)
    loop.run_until_complete(coro)
    asyncio.async(handle_user_input(loop))

    try:
        loop.run_forever()
    finally:
        loop.close()


def parse_command_line(description):
    """
        A function to parse the command line options given to the program
    :param description: description of the program
    :return: A tuple of args
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('host', help='IP or hostname')
    parser.add_argument('-p', metavar='port', type=int, default=7000,
                        help='TCP port (default 7000)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address


if __name__ == "__main__":
    address = parse_command_line('Chat Client')
    run_client(address[0], address[1])
