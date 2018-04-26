import asyncio
import argparse
import socket
import struct
import json
import time
import calendar
import datetime
import ssl


class ChatClient(asyncio.Protocol):
    def __init__(self):
        self.length = 0
        self.login_status = False
        self.data = ''
        self.overflow = b''
        self.username = ''
        self.feed = False

    def connection_made(self, transport):
        print('Connection Made')
        self.transport = transport

    def send_message(self, data):
        self.transport.write(data)

    def data_received(self, data):
        if self.overflow:
            self.length = struct.unpack('!I', self.overflow[0:4])[0]
            new_data = self.overflow[4: self.length + 4]
            data = new_data + data
            self.overflow = b''

        if self.data == '' and self.length == 0:
            self.length = struct.unpack("!I", data[0:4])[0]
            data = data[4: self.length + 4]
        if data == data[0:4]:
            self.data = ''
        else:
            self.data += data.decode('ascii')

        if len(self.data) > self.length:
            self.overflow += self.data[:self.length].encode('ascii')
            self.data = ''

        if len(self.data) == self.length:
            recv_data = json.loads(self.data)

            if 'USERNAME_ACCEPTED' in recv_data:
                if recv_data['USERNAME_ACCEPTED']:
                    if 'USER_LIST' in recv_data:
                        self.username = recv_data['USER_LIST'][-1] # does new name append to end?

                    print('  ')
                    print("Your Username is: {}".format(self.username))
                    print('  ')
                    self.login_status = True

                if not recv_data['USERNAME_ACCEPTED']:
                    print('Invalid Username or No Previously Held Username')

            if "INFO" in recv_data:
                print('-----{}-----'.format(recv_data['INFO']))
                print('  ')

            if "USER_LIST" in recv_data:
                print('  ')
                print("-----Current Users-----")
                print("-----------------------")
                for i in recv_data["USER_LIST"]:
                    print('>>> {}  Status: Online'.format(i))
                print("-----------------------")
                print('  ')

            if 'USERS_JOINED' in recv_data:
                if recv_data['USERS_JOINED'] != [] and self.username not in recv_data['USERS_JOINED']:
                    print('  ')
                    print("-----------------------")
                    for i in recv_data['USERS_JOINED']:
                        print('{} has joined the chatroom'.format(i))
                    print("-----------------------")
                    print('  ')

            if 'USERS_LEFT' in recv_data:
                if recv_data['USERS_LEFT'] != []:
                    print('  ')
                    print("-----------------------")
                    for i in recv_data["USERS_LEFT"]:
                        print('{} has left the chatroom'.format(i))
                    print("-----------------------")
                    print('  ')

            if 'ERROR' in recv_data:
                print('  ')
                print("-----------------------")
                print('>>> Error message received: {}'.format(recv_data['ERROR']))
                print("-----------------------")
                print('  ')

            if 'MESSAGES' in recv_data:
                if not self.feed:
                    print('--------Messages--------')
                    print('------------------------')
                    if recv_data['MESSAGES']:
                        for i in recv_data['MESSAGES']:
                            time_stamp = datetime.datetime.fromtimestamp(i[2]).strftime('%X')
                            if i[1] == self.username:
                                print('----- Private Message -----')
                                print('>>>> [{}]:    (Sent at {})'.format(i[0], i[3], time_stamp))
                                print('----------------------------')
                            if i[1] == 'ALL':
                                print('[{}]: {}   (Sent at {})'.format(i[0], i[3], time_stamp))
                    self.feed = True

                else:
                    for i in recv_data['MESSAGES']:
                        time_stamp = datetime.datetime.fromtimestamp(i[2]).strftime('%X')
                        if i[1] == self.username:
                            print('----- Private Message -----')
                            print('>>>> [{}]: {}    (Sent at {})'.format(i[0], i[3], time_stamp))
                            print('----------------------------')
                        if i[1] == 'ALL':
                            print('[{}]: {}   (Sent at {})'.format(i[0], i[3], time_stamp))

            if 'FILE_LIST' in recv_data:
                print('  ')
                print('-------File List-------')
                print("-----------------------")
                for i in recv_data['FILE_LIST']:
                    print('>>> {}'.format(i))
                print("-----------------------")
                print('  ')

            if 'FILE_DOWNLOAD' in recv_data:
                if recv_data['FILE_DOWNLOAD'][1] == 'ERROR':
                    print('  ')
                    print("-----------------------")
                    print(recv_data['FILE_DOWNLOAD'][0])
                    print("-----------------------")
                    print('  ')
                else:
                    print('  ')
                    print("-----------------------")
                    try:
                        open_file = open(recv_data['FILE_DOWNLOAD'][1], 'w+')
                        open_file.write(recv_data['FILE_DOWNLOAD'][0])
                        open_file.close()
                        print('>>> {} Downloaded Successfully'.format(recv_data['FILE_DOWNLOAD'][1]))
                    except exec as e:
                        print('>>> Error: {} while Downloading File {}'.format(e, recv_data['FILE_DOWNLOAD'][1]))
                    print("-----------------------")
                    print('  ')

            if 'FILE_UPLOAD' in recv_data:
                if recv_data['FILE_UPLOAD'][1] == 'ERROR':
                    print('  ')
                    print("-----------------------")
                    print('File {} already exists on the Server'.format(recv_data['FILE_UPLOAD'][0]))
                    print("-----------------------")
                    print('  ')
                else:
                    print('  ')
                    print("-----------------------")
                    print('>>> {} Uploaded Successfully'.format(recv_data['FILE_UPLOAD'][0]))
                    print("-----------------------")
                    print('  ')

            if 'IP' in recv_data:
                    print('  ')
                    print("-----------------------")
                    print('>>> {}'.format(recv_data['IP']))
                    print("-----------------------")
                    print('  ')

            self.data = ''
            self.length = 0


@asyncio.coroutine
def handle_user_input(loop, client):
    login_data = {'USERNAME': ''}
    default_message = {'MESSAGES': []}
    file_upload = {'FILE_UPLOAD': ()}
    file_download = {'FILE_DOWNLOAD': ''}
    ip_address = {'IP': ()}
    ip = socket.gethostbyname(socket.gethostname())

    ip_address['IP'] = (ip, 'CHECK')
    data_json = json.dumps(ip_address)
    byte_json = data_json.encode('ascii')
    byte_count = struct.pack("!I", len(byte_json))
    client.send_message(byte_count)
    client.send_message(byte_json)
    yield from asyncio.sleep(1)

    while not client.login_status:
        message = yield from loop.run_in_executor(None, input, "> Enter your username: ")
        if message == "quit" or message == 'exit':
            loop.stop()
            return

        login_data["USERNAME"] = message
        data_json = json.dumps(login_data)
        byte_json = data_json.encode('ascii')
        byte_count = struct.pack("!I", len(byte_json))

        client.send_message(byte_count)
        client.send_message(byte_json)

        yield from asyncio.sleep(1)

        login_data['USERNAME'] = ''

    while client.login_status:
        message = yield from loop.run_in_executor(None, input, "{} >>> ".format(client.username))

        if message == "quit" or message == 'exit':
            loop.stop()
            return
        if message:
            if message[0] == '/':
                if message.split(' ', maxsplit=1)[0][1:] == 'help':
                    list_commands()

                elif message.split(' ', maxsplit=1)[0][1:] == 'w':
                    username = message.split(' ', maxsplit=2)[1]
                    private_message = message.split(' ', maxsplit=2)[2]
                    complete_message = (client.username, username, calendar.timegm(time.gmtime()),
                                        private_message)
                    default_message['MESSAGES'].append(complete_message)
                    data_json = json.dumps(default_message)
                    byte_json = data_json.encode('ascii')
                    byte_count = struct.pack('!I', len(byte_json))

                    client.send_message(byte_count)
                    client.send_message(byte_json)

                elif message.split(' ', maxsplit=1)[0][1:] == 'file':
                    filename = message.split(' ', maxsplit=1)[1]
                    try:
                        open_file = open(filename, 'r')
                        data = open_file.read()
                        file_upload['FILE_UPLOAD'] = (filename, data)
                        data_json = json.dumps(file_upload)
                        byte_json = data_json.encode('ascii')
                        byte_count = struct.pack('!I', len(byte_json))
                        client.send_message(byte_count)
                        client.send_message(byte_json)
                    except exec as e:
                        print('-----------------------')
                        print('File Upload Error: {}'.format(e))
                        print('-----------------------')

                elif message.split(' ', maxsplit=1)[0][1:] == 'file_download':
                    filename = message.split(' ', maxsplit=1)[1]
                    file_download['FILE_DOWNLOAD'] = filename
                    data_json = json.dumps(file_download)
                    byte_json = data_json.encode('ascii')
                    byte_count = struct.pack('!I', len(byte_json))
                    client.send_message(byte_count)
                    client.send_message(byte_json)

                elif message.split(' ', maxsplit=1)[0][1:] == 'save':
                    ip_address['IP'] = ('SAVE', ip)
                    data_json = json.dumps(ip_address)
                    byte_json = data_json.encode('ascii')
                    byte_count = struct.pack('!I', len(byte_json))
                    client.send_message(byte_count)
                    client.send_message(byte_json)

                else:
                    complete_message = (client.username, 'ALL', calendar.timegm(time.gmtime()), message)
                    default_message['MESSAGES'].append(complete_message)
                    data_json = json.dumps(default_message)
                    byte_json = data_json.encode('ascii')
                    byte_count = struct.pack('!I', len(byte_json))
                    client.send_message(byte_count)
                    client.send_message(byte_json)
                yield from asyncio.sleep(1)

            else:
                complete_message = (client.username, 'ALL', calendar.timegm(time.gmtime()), message)
                default_message['MESSAGES'].append(complete_message)
                data_json = json.dumps(default_message)
                byte_json = data_json.encode('ascii')
                byte_count = struct.pack('!I', len(byte_json))
                client.send_message(byte_count)
                client.send_message(byte_json)
                yield from asyncio.sleep(1)

        default_message['MESSAGES'] = []
        file_upload['FILE_UPLOAD'] = ()
        file_download['FILE_DOWNLOAD'] = ''
        ip_address["IP"] = ()


def run_client(host, port, cafile):
    loop = asyncio.get_event_loop()
    client = ChatClient()

    if cafile:
        print('Encrpyted')
        print(cafile)
        purpose = ssl.Purpose.SERVER_AUTH
        context = ssl.create_default_context(purpose, cafile=cafile)
        coro = loop.create_connection(lambda: client, host, port, ssl=context, server_hostname='localhost')
        loop.run_until_complete(coro)
        asyncio.async(handle_user_input(loop, client))

    else:
        coro = loop.create_connection(lambda: client, host, port)
        loop.run_until_complete(coro)
        asyncio.async(handle_user_input(loop, client))

    try:
        loop.run_forever()
    finally:
        loop.close()


def list_commands():
    print('  ')
    print('Chat Client Commands')
    print('-----------------------')
    print("Whisper: Send a online user a private message: /w username (message)")
    print('Current Users: Get a list of all current online users: /users')
    print('File Transfer (Upload): Transfer a file to the server: /file (file path)')
    print('File Transfer (Download): Prints out the contents of a file: /file_download (file name)')
    print('File List: Lists all files currently stored on a server: /file_list')
    print('Save Username: Save your current username to the server to auto login at this ip address: /save')
    print('Exit: Close the client: quit or exit')
    print('Commands: Lists all commands for the Client: /help')
    print('-----------------------')
    print('  ')


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
    parser.add_argument('-a', metavar='cafile', default=None,
                        help='Set up a basic encrypted Connection')
    args = parser.parse_args()
    address = (args.host, args.p, args.a)
    return address


if __name__ == "__main__":
    address = parse_command_line('Chat Client')
    run_client(address[0], address[1], address[2])
