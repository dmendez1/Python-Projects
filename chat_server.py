import asyncio
import requests
import requests_oauthlib
import json

class ChatServerProtocol(asyncio.Protocol):

    clients = {}
    rooms = [{'name': 'public',
              'owner': 'system',
              'description': 'The public room which acts as broadcast, all logged-in users are in public room by default'}
             ]

    def __init__(self):
        self._pieces = []

    def _handle_command(self):
        command = ''.join(self._pieces)
        self._pieces = []

        if command.startswith('/lru'):

            lru = [r['login-name'] for r in ChatServerProtocol.clients.values() if r['login-name']]
            response = '/lru '
            for user in lru:
                response += (f'{user}, ')

            response.rstrip(', ')
            response = ''.join([response, '$'])
            self._transport.write(response.encode('utf-8'))

        elif command.startswith('/login '):


            login_name = command.lstrip('/login').rstrip('$').strip()

            logins = [v['login-name'] for v in ChatServerProtocol.clients.values()]
            if login_name in logins:
                response = '/login already exists$'
            else:
                record = ChatServerProtocol.clients[self._transport]
                record['login-name'] = login_name
                response = '/login success$'

            self._transport.write(response.encode('utf-8'))

        elif command.startswith('/lrooms '):


            room_msgs = ['{}&{}&{}'.format(r['name'], r['owner'], r['description']) for r in ChatServerProtocol.rooms]
            response = '/lrooms {}$'.format('\n'.join(room_msgs))
            self._transport.write(response.encode('utf-8'))

        elif command.startswith('/post '):

                room, message = command.lstrip('/post').rstrip('$').split('&')

                carry = [k for k, v in ChatServerProtocol.clients.items() if room.strip() in v['rooms']]

                outgoing_message = '/MSG {}$'.format(message)
                for transport in carry:
                    transport.write(outgoing_message.encode('utf-8'))

        elif command.startswith('/make '):
            duplicated_room = False
            rname, lname, description = command.lstrip('/make ').rstrip('$').split('&')
            for r in ChatServerProtocol.rooms:
                if r['name'] == rname:
                    duplicated_room = True
            if duplicated_room == False:
                messages = {'name': rname,
                        'owner': lname,
                        'description': description}
                ChatServerProtocol.rooms.append(messages)
                record = ChatServerProtocol.clients[self._transport]
                room_list = []
                for x in record['rooms']:
                    room_list.append(x)
                room_list.append(rname)
                record['rooms'] = room_list
                message = '\nRoom created$'
                self._transport.write(message.encode('utf-8'))
            else:
                message = '\nRoom already exists!\t Try another name.$'
                self._transport.write(message.encode('utf-8'))

        elif command.startswith('/join '):
            identified = False
            room = command.lstrip('/join ').rstrip('$')
            for x in ChatServerProtocol.rooms:
                if x['name'] == room:
                    identified = True
                    break
            if identified:
                record = ChatServerProtocol.clients[self._transport]
                room_list = []
                for x in record['rooms']:
                    room_list.append(x)
                room_list.append(room)
                record['rooms'] = room_list
                message = 'Congratulations! You have joined the room successfully$'
                self._transport.write(message.encode('utf-8'))
            else:
                message = 'The room you are trying to join does not exist$'
                self._transport.write(message.encode('utf-8'))

        elif command.startswith('/leave '):
            linked = False
            log_username = command.lstrip('/leave ').rstrip('$')
            for x in ChatServerProtocol.clients[self._transport]:
                if x == log_username:
                    linked = True
                    break
            if linked:
                record = ChatServerProtocol.clients[self._transport]
                room_list = []
                for x in record['rooms']:
                    room_list.remove(x)
                record['rooms'] = room_list
                message = 'Bye! You left the room successfully$'
                self._transport.write(message.encode('utf-8'))
            else:
                message = 'Come back! You did not leave the room successfully$'
                self._transport.write(message.encode('utf-8'))

        elif command.startswith('/direct '):
            sender, receiver, direct_message = command.lstrip('/direct ').rstrip('$').split('&')
            logins = [v['login-name'] for v in ChatServerProtocol.clients.values()]
            if receiver in logins:
                send_message = '/MSG {}$'.format(direct_message)
                for user in logins:
                    if user == receiver:
                        carry = [k for k, v in ChatServerProtocol.clients.items() if receiver.strip() in v['login-name']]
                        for transport in carry:
                            transport.write(send_message.encode('utf-8'))
                    else:
                        print('User {} did not successfully send a message to {}'.format(sender, receiver))
                response = 'Your message has been sent$'
            else:
                response = 'I am sorry, I do not recognize that user$'
            self._transport.write(response.encode('utf-8'))

    def connection_made(self, transport: asyncio.Transport):
        """Called on new client connections"""
        self._remote_addr = transport.get_extra_info('peername')
        print('[+] client {} connected.'.format(self._remote_addr))
        self._transport = transport
        ChatServerProtocol.clients[transport] = {'remote': self._remote_addr, 'login-name': None, 'rooms': ['public']}

    def data_received(self, data):
        """Handle data"""
        self._pieces.append(data.decode('utf-8'))
        if ''.join(self._pieces).endswith('$'):
            self._handle_command()

    def connection_lost(self, exc):
        """remote closed connection"""
        print('[-] lost connection to {}'.format(ChatServerProtocol.clients[self._transport]))
        self._transport.close()

class ChatServer:
    LOCAL_HOST = '0.0.0.0'

    def __init__(self, port):
        self._port: int = port

    def listen(self):
        """start listening"""
        pass

    def start(self):
        """start"""
        loop = asyncio.get_event_loop()
        server_coro = loop.create_server(lambda: ChatServerProtocol(),
                                         host=ChatServer.LOCAL_HOST,
                                         port=self._port)

        loop.run_until_complete(server_coro)
        loop.run_forever()


if __name__ == '__main__':
    chat_server = ChatServer(port=8080)
    chat_server.start()
