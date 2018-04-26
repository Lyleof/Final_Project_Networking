"""chat_server.py

Author:            Walter Hill, FInn Jensen
Class:             Network Programming
Assignment:        Final Project
Date Assigned:     4/17/18
Due date:          4/26/18

Description: An asynchronous client and server object to maintain a terminal chat application

-Worked with Finn Jensen
Champlain College CSI-235, Spring 2018
This code builds off skeleton code written by
Prof. Joshua Auerbach (jauerbach@champlain.edu)
"""

import asyncio
import argparse
import json
import struct
import ssl


class ChatServer(asyncio.Protocol):
    """
      A class to receive clients, their messages, and to communicate back to them asynchronously.

      :Variables:
                message_list(dict): List of message keys with message data within as a list
                user_list(dict): list of users within the user_list key
                transport_list(dict): list of client transports within the con_list key
                new_logon(bool): Toggled when a new user connects for the first time
                length(int): Holds the length of a given message from the server
                data(str): Stores the data coming over the network from the server
                overflow (byte str): Extraneous data from the server stored here
                user(str): stores this client's username
                saved_users(dict) = List of ip keys and their remembered username
                file_list(bool): toggles whether tho display the entire message feed
    """
    messages_list = {'MESSAGES': []}
    user_list = {"USER_LIST": []}
    transport_list = {"CON_LIST": []}
    new_logon = False

    def __init__(self):
        self.user = ''
        self.data = ''
        self.length = 0
        self.overflow = b''
        self.saved_users = {}
        self.file_list = {'FILE_LIST': []}

    def connection_made(self, transport):
        """
          A function to accept a two-way connection with a client
          :param: Transport: Networking object that allows sending to the client
          :return: None
        """

        self.transport = transport
        self.new_logon = True
        self.command = False
        self.logout = False
        ChatServer.transport_list['CON_LIST'].append(self.transport)
        print('Connection Made')

    def pack_message(self, full_data):
        """
          A function to receive raw response data and
          send that data to the correct clients in the correct format.
          :param: full_data: raw data to be packaged sent across the socket to the correct clients
          :return: None
        """
        data_json = json.dumps(full_data)
        print(full_data)

        if self.new_logon:
            print('New Logon')
            joined_data = {}
            joined_data["USERS_JOINED"] = []
            joined_data["USERS_JOINED"] = full_data["USERS_JOINED"]

            joined_json = json.dumps(joined_data)

            for i in range(len(ChatServer.transport_list['CON_LIST'])):
                if ChatServer.transport_list['CON_LIST'][i] == self.transport:
                    byte_json = data_json.encode('ascii')
                    byte_count = struct.pack('!I', len(byte_json))

                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_count)
                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_json)
                    self.new_logon = False
                else:
                    byte_json = joined_json.encode('ascii')
                    print('Else new Logon statment')
                    print(joined_json)
                    byte_count = struct.pack('!I', len(byte_json))

                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_count)
                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_json)
        elif self.logout:
            left_data = {}
            left_data["USERS_LEFT"] = []
            left_data["USERS_LEFT"] = full_data["USERS_LEFT"]

            left_json = json.dumps(left_data)

            for i in range(len(ChatServer.transport_list['CON_LIST'])):
                if ChatServer.transport_list['CON_LIST'][i] != self.transport:
                    byte_json = left_json.encode('ascii')
                    print(byte_json)
                    byte_count = struct.pack('!I', len(byte_json))
                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_count)
                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_json)

            self.logout = False
        elif self.command:
            for i in range(len(ChatServer.transport_list['CON_LIST'])):
                if ChatServer.transport_list['CON_LIST'][i] == self.transport:
                    byte_json = data_json.encode('ascii')
                    print(byte_json)
                    byte_count = struct.pack('!I', len(byte_json))

                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_count)
                    self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_json)
            self.command = False
        else:
            print('Basic Messages')
            msg_data = {'MESSAGES': []}
            if full_data['MESSAGES']:
                msg_data["MESSAGES"].append(full_data["MESSAGES"][-1])

            # msg_data["MESSAGES"] = msg_data["MESSAGES"][-1]
            # print(msg_data["MESSAGES"])
            msg_json = json.dumps(msg_data)

            byte_json = msg_json.encode('ascii')
            print(byte_json)
            byte_count = struct.pack('!I', len(byte_json))

            for i in range(len(ChatServer.transport_list['CON_LIST'])):
                self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_count)
                self.send_message(ChatServer.transport_list['CON_LIST'][i], byte_json)

    def send_message(self, client_transport, data):
        """
          A function to send json packaged and encoded data to the client
          :param: Data: encoded data to send across the socket to the client
          :return: None
        """
        client_transport.write(data)

    def data_received(self, data):
        """
          A function to receive messages from clients.
          These messages can range from messages to special user commands
          :param: Data: encoded data sent across the socket to the client
          :return: None
        """
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
            full_data = {}

            if 'USERNAME' in recv_data:
                print('Username recivied')
                result = self.username_check(recv_data['USERNAME'])
                full_data['USERNAME_ACCEPTED'] = result
                if result:
                    full_data['USERS_JOINED'] = []
                    ChatServer.user_list['USER_LIST'].append(recv_data['USERNAME'])
                    self.user = recv_data['USERNAME']
                    full_data['USERS_JOINED'].append(self.user)
                    full_data['INFO'] = 'Welcome the CYOSP Chatroom'
                    full_data['USER_LIST'] = ChatServer.user_list['USER_LIST']
                    full_data['MESSAGES'] = ChatServer.messages_list['MESSAGES']

            if 'IP' in recv_data:
                if recv_data['IP'][1] == 'CHECK':
                    result = self.ip_check(recv_data['IP'][0])
                    if result:
                        full_data['USERNAME_ACCEPTED'] = True
                        ChatServer.user_list['USER_LIST'].append(self.saved_users[recv_data['IP'][0]])
                        self.user = self.saved_users[recv_data['IP'][0]]
                        full_data['USERS_JOINED'].append(self.user)
                        full_data['INFO'] = 'Welcome the CYOSP Chatroom'
                        full_data['USER_LIST'] = ChatServer.user_list['USER_LIST']
                        full_data['MESSAGES'] = ChatServer.messages_list['MESSAGES']
                if recv_data['IP'][1] == 'SAVE':
                    self.command = True
                    result = self.ip_check(recv_data['IP'][0])
                    if result:
                        full_data['IP'] = 'A Username is Already Saved to this ip Address'

                    else:
                        full_data['IP'] = 'Username Successfully Saved to ip Address'
                        self.saved_users[recv_data['IP'][0]] = self.user

            if 'MESSAGES' in recv_data:
                print(recv_data['MESSAGES'])
                for i in recv_data['MESSAGES']:
                    print(i)
                    if i[3] == '/users':
                        print('Command Entered')
                        full_data['USER_LIST'] = ChatServer.user_list['USER_LIST']
                        self.command = True
                    if i[3] == '/file_list':
                        print('Command Entered')
                        full_data['FILE_LIST'] = self.file_list['FILE_LIST']
                        self.command = True
                    if not self.command:
                        if i not in ChatServer.messages_list['MESSAGES']:
                            ChatServer.messages_list['MESSAGES'].append(i) # get most recent msg?
                        print(ChatServer.messages_list['MESSAGES'])
                        full_data['MESSAGES'] = ChatServer.messages_list['MESSAGES']

            if 'FILE_DOWNLOAD' in recv_data:
                self.command = True
                if recv_data['FILE_DOWNLOAD'] in self.file_list['FILE_LIST']:
                    try:
                        open_file = open(recv_data['FILE_DOWNLOAD'], 'r')
                        data = open_file.read()
                        full_data['FILE_DOWNLOAD'] = (data, recv_data['FILE_DOWNLOAD'])

                    except exec as e:
                        full_data['ERROR'] += e
                else:
                    full_data['FILE_DOWNLOAD'] = ('File not on Server', 'ERROR')

            if 'FILE_UPLOAD' in recv_data:
                self.command = True
                if recv_data['FILE_UPLOAD'][0] in self.file_list['FILE_LIST']:
                    full_data['FILE_UPLOAD'] = (recv_data['FILE_UPLOAD'][0],
                                                'ERROR')
                else:
                    try:
                        open_file = open(recv_data['FILE_UPLOAD'][0], 'w+')
                        open_file.write(recv_data['FILE_UPLOAD'][1])
                        open_file.close()
                        full_data['FILE_UPLOAD'] = (recv_data['FILE_UPLOAD'][0], 'SUCCESS')

                    except exec as e:
                        full_data['ERROR'] += e

            if full_data:
                self.pack_message(full_data)

            self.data = ''
            self.length = 0

    def connection_lost(self, exc):
        """
          A function to handle disconnects from clients.
          :param: exc: Exception parameter
          :return: None
        """
        ChatServer.transport_list['CON_LIST'].remove(self.transport)

        full_data = {}
        full_data['MESSAGES'] = []
        full_data['USERS_LEFT'] = []

        self.logout = True

        if exc:
            if self.user:
                ChatServer.user_list['USER_LIST'].remove(self.user)
                full_data['USERS_LEFT'].append(self.user)
                full_data['ERROR'] = '{} has left unexpectedly. Error: {}'.format(self.user, exc)
        else:
            full_data['USERS_LEFT'].append(self.user)
            ChatServer.user_list['USER_LIST'].remove(self.user)
        self.pack_message(full_data)

    def username_check(self, name):
        """
          A function to validate a username. Handles new users and old ones by ip
]          :param: Name(str): username
          :return: a True or False boolean
        """
        if name not in ChatServer.user_list["USER_LIST"]:
            for k, v in self.saved_users.items():
                if v == name:
                    return False
            return True
        else:
            return False

    def ip_check(self, ip):
        for k, v in self.saved_users.items():
            if k == ip:
                return True

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
    parser.add_argument('-a', metavar='certfile', default=None,
                        help='Set up a basic encrypted connection')
    args = parser.parse_args()
    address = (args.host, args.p)

    return address, args.a


if __name__ == '__main__':
    arguments = parse_command_line('asyncio server using callbacks')

    if arguments[1]:
        purpose = ssl.Purpose.CLIENT_AUTH
        context = ssl.create_default_context(purpose, cafile=None)
        context.load_cert_chain(arguments[1])
        loop = asyncio.get_event_loop()
        coro = loop.create_server(ChatServer, *arguments[0], ssl=context)
        server = loop.run_until_complete(coro)
        print('Listening Encrypted at {}'.format(arguments[0]))

    else:
        loop = asyncio.get_event_loop()
        coro = loop.create_server(ChatServer, *arguments[0])
        server = loop.run_until_complete(coro)
        print('Listening at {}'.format(arguments[0]))

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()