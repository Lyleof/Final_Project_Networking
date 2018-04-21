import asyncio
import argparse
import json
import struct

class ChatServer(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address))
        self.user_list = {}
        self.user_list["USER_LIST"] = []
        self.messages = {}
        self.validate_user = {}
        self.validate_user["USERNAME_ACCEPTED"] = "False"

    def send_message(self, data):
        byte_count = struct.pack('!I', len(data))
        self.transport.write(byte_count)
        self.transport.write(data)

    def data_received(self, data):
        self.data += data
        print(self.data[0:4])
        print(self.data[5:])

        if len(self.data[4:]) == struct.unpack('!I', self.data[0:4])[0]:
            print("all data got")
            recv_data = json.loads(self.data[4:].decode('ascii'))
            print(recv_data)

            self.username_check(recv_data['USERNAME'])

            # TODO: Create a single json object to send everything
            data_json = json.dumps(self.validate_user)
            # data_json += json.dumps(self.user_list)
            byte_json = data_json.encode('ascii')

            print(byte_json)
            self.send_message(byte_json)

            self.data = b''


    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address, exc))
        elif self.data:
            print('Client {} sent {} but then closed'.format(self.address, self.data))
        else:
            print('Client {} closed socket'.format(self.address))

    def username_check(self, name):

        if name not in self.user_list["USER_LIST"]:
            print("Hi new user TRUE")
            self.user_list["USER_LIST"].append(name)
            print(self.user_list["USER_LIST"])
            self.validate_user["USERNAME_ACCEPTED"] = "True"
        else:
            self.validate_user["USERNAME_ACCEPTED"] = "False"
            print("That name is taken: FALSE")


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


if __name__ == '__main__':
    address = parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    coro = loop.create_server(ChatServer, *address)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()