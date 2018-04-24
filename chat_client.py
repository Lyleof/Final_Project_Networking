import asyncio
import argparse
import socket
import struct
import json
import time
import calendar
import datetime


class ChatClient(asyncio.Protocol):
    def __init__(self):
        self.length = 0
        self.login_status = False
        self.data = ''
        self.username = ''
        self.feed = False

    def connection_made(self, transport):
        self.transport = transport

    def send_message(self, data):
        self.transport.write(data)

    def data_received(self, data):
        if self.data == '':
            self.length = struct.unpack("!I", data[0:4])[0]
            data = data[4: self.length + 4]

        self.data += data.decode('ascii')

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
                print("-----Current Users-----")
                print("-----------------------")
                for i in recv_data["USER_LIST"]:
                    print('>>> {}  Status: Online'.format(i))
                print("-----------------------")

            if 'USERS_JOINED' in recv_data:
                print("-----------------------")
                for i in recv_data['USERS_JOINED']:
                    print('{} has joined the chatroom'.format(i))
                print("-----------------------")
                # print('  ')

            if 'USERS_LEFT' in recv_data:
                print("-----------------------")
                for i in recv_data["USERS_LEFT"]:
                    print('{} has left the chatroom'.format(i))
                print("-----------------------")

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
                if recv_data['FILE_DOWNLOAD'][2] == 'ERROR' and self.username == recv_data['FILE_DOWNLOAD'][0]:
                    print('  ')
                    print("-----------------------")
                    print(recv_data['FILE_DOWNLOAD'][1])
                    print("-----------------------")
                    print('  ')
                if self.username == recv_data['FILE_DOWNLOAD'][0]:
                    print('  ')
                    print("-----------------------")
                    try:
                        open_file = open(recv_data['FILE_DOWNLOAD'][2], 'w+')
                        open_file.write(recv_data['FILE_DOWNLOAD'][1])
                        open_file.close()
                        print('>>> {} Downloaded Successfully'.format(recv_data['FILE_DOWNLOAD'][2]))
                    except exec as e:
                        print('>>> Error: {} while Downloading File {}'.format(e, recv_data['FILE_DOWNLOAD'][2]))
                    print("-----------------------")
                    print('  ')

            if 'FILE_UPLOAD' in recv_data:
                if recv_data['FILE_UPLOAD'][2] == 'ERROR' and recv_data['FILE_UPLOAD'][0] == self.username:
                    print('  ')
                    print("-----------------------")
                    print('File {} already exists on the Server'.format(recv_data['FILE_UPLOAD'][1]))
                    print("-----------------------")
                    print('  ')
                if recv_data['FILE_UPLOAD'][0] == self.username:
                    print('  ')
                    print("-----------------------")
                    print('>>> {} Uploaded Successfully'.format(recv_data['FILE_UPLOAD'][1]))
                    print("-----------------------")
                    print('  ')

            if 'IP' in recv_data:
                if recv_data['IP'][0] == self.username:
                    print('  ')
                    print("-----------------------")
                    print('>>> {}'.format(recv_data['IP'][1]))
                    print("-----------------------")
                    print('  ')

            self.data = ''

# TODO: Chnage Username existsing to serverside
@asyncio.coroutine
def handle_user_input(loop, client):
    login_data = {'USERNAME': ''}
    default_message = {'MESSAGES': []}
    file_upload = {'FILE_UPLOAD': ()}
    file_download = {'FILE_DOWNLOAD': ''}
    ip_address = {'IP': ()}
    ip = socket.gethostbyname(socket.gethostname())

    while not client.login_status:
        choice = input('Create New User[Y] or Check for Existing Username[N]:  ')

        if choice == 'N':
            ip_address['IP'] = ('', ip)
            data_json = json.dumps(ip_address)
            byte_json = data_json.encode('ascii')
            byte_count = struct.pack("!I", len(byte_json))
            client.send_message(byte_count)
            client.send_message(byte_json)

        if choice == 'Y':
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

            client.username = message

        login_data['USERNAME'] = ''
        ip_address['IP'] = ()

    while client.login_status:
        message = yield from loop.run_in_executor(None, input, "{} >>> ".format(client.username))

        if message == "quit" or message == 'exit':
            loop.stop()
            return

        if message[0] == '/':
            if message.split(' ', maxsplit=1)[0][1:] == 'help':
                list_commands()

            if message.split(' ', maxsplit=1)[0][1:] == 'w':
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

            if message.split(' ', maxsplit=1)[0][1:] == 'file':
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

            if message.split(' ', maxsplit=1)[0][1:] == 'file_download':
                filename = message.split(' ', maxsplit=1)[1]
                file_download['FILE_DOWNLOAD'] = filename
                data_json = json.dumps(file_download)
                byte_json = data_json.encode('ascii')
                byte_count = struct.pack('!I', len(byte_json))
                client.send_message(byte_count)
                client.send_message(byte_json)

            if message.split(' ', maxsplit=1)[0][1:] == 'save':
                ip_address['IP'] = (message, ip)
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

        default_message['MESSAGES'] = []
        file_upload['FILE_UPLOAD'] = ()
        file_download['FILE_DOWNLOAD'] = ''
        ip_address["IP"] = ()


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
    parser.add_argument('-p', metavar='port', type=int, default=9000,
                        help='TCP port (default 7000)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address


if __name__ == "__main__":
    address = parse_command_line('Chat Client')
    run_client(address[0], address[1])
