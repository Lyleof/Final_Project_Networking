import asyncio
import argparse
import json
import struct


class ChatServer(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.user = ''
        self.data = b''
        self.user_list = {"USER_LIST": []}
        self.saved_users = {}
        self.messages = {'MESSAGES': []}
        self.file_list = {'FILE_LIST': []}

    def send_message(self, data):
        byte_count = struct.pack('!I', len(data))
        self.transport.write(byte_count)
        self.transport.write(data)

    def data_received(self, data):
        self.data += data
        if len(self.data[4:]) == struct.unpack('!I', self.data[0:4])[0]:
            recv_data = json.loads(self.data[4:].decode('ascii'))
            full_data = {}

            if 'USERNAME' in recv_data:
                result = self.username_check(recv_data['USERNAME'])
                full_data['USERNAME_ACCEPTED'] = result
                if result:
                    self.user_list['USER_LIST'].append(recv_data['USERNAME'])
                    full_data['USER_JOINED'].append(recv_data['USERNAME'])
                    full_data['INFO'] = 'Welcome the CYOSP Chatroom'
                    full_data['USER_LIST'] = self.user_list['USER_LIST']
                    full_data['MESSAGES'] = self.messages['MESSAGES']
                    self.user = recv_data['USERNAME']

            if 'IP' in recv_data:
                if not recv_data['IP'][0]:
                    for k, v in self.saved_users.items():
                        if k == recv_data['IP'][1]:
                            full_data['USERNAME_ACCEPTED'] = True
                            full_data['USERNAME'] = v
                else:
                    for k, v in self.saved_users.items():
                        if k == recv_data['IP'][1]:
                            full_data['IP'] = (self.user, 'A Username is already save to this ip address')
                    if not full_data['IP']:
                        self.saved_users[recv_data['IP'][1]] = self.user
                        full_data['IP'] = (self.user, 'Username save to Server')

            if 'MESSAGES' in recv_data:
                if recv_data['MESSAGES'] == '/users':
                    full_data['USER_LIST'] = self.user_list['USER_LIST']
                if recv_data['MESSAGES'] == '/file_list':
                    full_data['FILE_LIST'] = self.file_list['FILE_LIST']
                else:
                    self.messages['MESSAGES'].append(recv_data['MESSAGES'])
                    full_data['MESSAGES'] = self.messages['MESSAGES']

            if 'FILE_DOWNLOAD' in recv_data:
                if recv_data['FILE_DOWNLOAD'][0] in self.file_list['FILE_LIST']:
                    try:
                        open_file = open(recv_data['FILE_DOWNLOAD'][0], 'r')
                        data = open_file.read()
                        full_data['FILE_DOWNLOAD'] = (self.user, data, recv_data['FILE_DOWNLOAD'][0])
                    except exec as e:
                        full_data['ERROR'] += e
                else:
                    full_data['FILE_DOWNLOAD'] = (self.user, 'File not on Server', 'ERROR')

            if 'FILE_UPLOAD' in recv_data:
                if recv_data['FILE_UPLOAD'][0] in self.file_list['FILE_LIST']:
                    full_data['FILE_UPLOAD'] = (self.user, recv_data['FILE_UPLOAD'][0],
                                                'ERROR')
                else:
                    try:
                        open_file = open(recv_data['FILE_UPLOAD'][0], 'w+')
                        open_file.write(recv_data['FILE_UPLOAD'][1])
                        open_file.close()
                        full_data['FILE_UPLOAD'] = (self.user, recv_data['FILE_UPLOAD'][0], 'SUCCESS')

                    except exec as e:
                        full_data['ERROR'] += e

            data_json = json.dumps(full_data)
            byte_json = data_json.encode('ascii')
            self.send_message(byte_json)

            self.data = b''

    def connection_lost(self, exc):
        full_data = {}
        if exc:
            full_data['USERS_LEFT'].append(self.user)
            full_data['ERROR'] += '{} has left unexpectedly. Error: {}'.format(self.user, exc)
        else:
            full_data['USERS_LEFT'].append(self.user)
        data_json = json.dumps(full_data)
        byte_json = data_json.encode('ascii')
        self.send_message(byte_json)

    def username_check(self, name):

        if name not in self.user_list["USER_LIST"]:
            for k, v in self.saved_users.items():
                if v == name:
                    return False
            return True
        else:
            return False


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