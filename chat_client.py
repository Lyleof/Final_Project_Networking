import asyncio
import argparse
import socket
import struct
import json
import time
import calendar


class ChatClient(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.login_status = False
        self.data = b''
        self.username = ''

    def send_message(self, data):
        self.transport.write(data)

    def data_received(self, data):
        self.data += data
        print(self.data[0:4])
        print(self.data[5:])
        if len(self.data[5:]) == struct.unpack('!I', self.data[0:4]):
            print("Full Data recived")
            self.data = json.loads(self.data[5:])
            if "USERNAME_ACCEPTED" in self.data:
                if self.data['USERNAME_ACCEPTED'] == 'true':

                    if "INFO" in self.data:
                        print('-----' + self.data['INFO'] + '-----')

                    print("Current Users")
                    print("-----------------------")
                    if "USER_LIST" in self.data:
                        for i in self.data["USER_LIST"]:
                            print(">>>" + i + '  Status: Online')
                    else:
                        print('No Users Online')
                    print("-----------------------")
                    print('  ')

                    print('Messages')
                    if 'MESSAGES' in self.data:
                        for i in self.data['MESSAGES']:
                            if i[2] == self.username:
                                print('----- Private Message -----')
                                print('>>>>' + i[0] + ': ' + i[4] + '   (Sent at ' + i[3] + ')')
                                print('----------------------------')
                            if i[2] == 'ALL':
                                print(i[0] + ': ' + i[4] + '   (Sent at ' + i[3] + ')')
                    else:
                        print('No recent Messages')

                    if 'USERS_JOINED' in self.data:
                        for i in self.data['USERS_JOINED']:
                            print(i + ' has joined the chatroom')

                    if 'USERS_LEFT' in self.data:
                        for i in self.data["USERS_LEFT"]:
                            print(i + ' has left the chatroom')

                    self.login_status = True

                else:
                    print('Sorry that username is not available at this moment please enter a new one')


@asyncio.coroutine
def handle_user_input(loop, client):
    login_data = {'USERNAME': ''}
    default_messgae = {'MESSAGES': ''}
    # ip = socket.gethostbyname(socket.gethostname())

    if not client.login_status:
        while True:
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
            client.username = message

    if client.login_status:
        while True:
            message = yield from loop.run_in_executor(None, input, "> ")
            if message == "quit" or message == 'exit':
                # Send disconnect message here
                loop.stop()
                return
            # Add whisper function here and extra command handling

            complete_message = (client.username, 'ALL', calendar.timegm(time.gmtime()), message)
            default_messgae['MESSAGES'] = complete_message
            data_json = json.dumps(default_messgae)
            byte_json = data_json.encode('ascii')
            byte_count = struct.pack('!I', len(byte_json))

            client.send_message(byte_count)
            client.send_message(byte_json)

            default_messgae['MESSAGES'] = ''



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
