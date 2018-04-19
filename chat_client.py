import asyncio
import argparse
import socket
import struct
import json


class ChatClient(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.login_status = False
        self.data = b''
        self.data_length = 0

    def send_message(self, data):
        self.transport.write(data)

    def data_received(self, data):
        self.data += data
        if len(self.data[5:]) == struct.unpack('!I', self.data[0:4]):
            print("Full Data recived")
            self.data = json.loads(self.data)
            if self.data["USERNAME_ACCEPTED"]:
                print('Username if entered')
                print("Current Users")
                print("-----------------------")
                for i in self.data["USER_LIST"]:
                    print(">>>" + i + '  Status: Online')




@asyncio.coroutine
def handle_user_input(loop, client):
    login_data = {'USERNAME': ''}
    #ip = socket.gethostbyname(socket.gethostname())

    if not client.login_status:
        while True:
            message = yield from loop.run_in_executor(None, input, "> Enter your username")
            if message == "quit" or message == 'exit':
                loop.stop()
                return

            login_data["USERNAME"] = message
            data_json = json.dumps(login_data)
            byte_json = data_json.encode('ascii')
            byte_count = struct.pack("!I", len(byte_json))

            client.send_message(byte_count)
            client.send_message(byte_json)



def run_client(host, port):
    loop = asyncio.get_event_loop()
    client = ChatClient()
    coro = loop.create_connection(lambda: client, host, port)
    loop.run_until_complete(coro)
    asyncio.async(handle_user_input(loop, client))

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
    parser.add_argument('-p', metavar='port', type=int, default=9000,
                        help='TCP port (default 7000)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address


if __name__ == "__main__":
    address = parse_command_line('Chat Client')
    run_client(address[0], address[1])
