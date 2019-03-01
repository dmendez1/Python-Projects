import asyncio
import threading
import requests
import requests_oauthlib
import json

class NotConnectedError(Exception):
    pass

class LoginError(Exception):
    pass

class LoginConflictError(Exception):
    pass

class CreationError(Exception):
    pass

class CreateConflictError(Exception):
    pass

class ChatClientProtocol(asyncio.Protocol):
    def __init__(self):
        self._pieces = []
        self._responses_q = asyncio.Queue()
        self._user_messages_q = asyncio.Queue()

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport

    def data_received(self, data):
        self._pieces.append(data.decode('utf-8'))

        if ''.join(self._pieces).endswith('$'):
            protocol_msg = ''.join(self._pieces).rstrip('$')

            if protocol_msg.startswith('/MSG '):
                user_msg = protocol_msg.lstrip('/MSG')
                asyncio.ensure_future(self._user_messages_q.put(user_msg))
            else:
                asyncio.ensure_future(self._responses_q.put(''.join(self._pieces).rstrip('$')))

            self._pieces = []

    def connection_lost(self, exc):
        self._transport.close()

class ChatClient:
    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._connected = False

    def disconnect(self):
        if not self._connected:
            raise NotConnectedError()

        self._transport.close()

    async def _connect(self):
        try:
            loop = asyncio.get_event_loop()
            self._transport, self._protocol = await loop.create_connection(
                lambda: ChatClientProtocol(),
                self._ip,
                self._port)

            self._connected = True
            print('connected to chat server')

        except ConnectionRefusedError:
            print('error connecting to chat server - connection refused')

        except TimeoutError:
            print('error connecting to chat server - connection timeout')

        except Exception as e:
            print('error connecting to chat server - fatal error')

    def connect(self):
        loop = asyncio.get_event_loop()
        try:
            asyncio.ensure_future(self._connect())

            loop.run_forever()
        except Exception as e:
            print(e)
        finally:
            print('{} - closing main event loop'.format(threading.current_thread().getName()))
            loop.close()

    async def lru(self):
        self._transport.write('/lru $'.encode('utf-8'))

        users = lru_response.lstrip('/lru ').split(', ')

        users = [u for u in users if u and u != '']

        return users

    async def login(self, login_name):
        self._transport.write('/login {}$'.format(login_name).encode('utf-8'))
        login_response = await self._protocol._responses_q.get()
        success = login_response.lstrip('/login ')

        if success == 'already exists':
            raise LoginConflictError()

        elif success != 'success':
            raise LoginError()

    async def lrooms(self):


        self._transport.write('/lrooms $'.encode('utf-8'))
        lrooms_response = await self._protocol._responses_q.get()

        lines = lrooms_response.lstrip('/lrooms ').split('\n')

        rooms = []
        for line in lines:
            room_attributes = line.split('&')
            rooms.append({'name': room_attributes[0], 'owner': room_attributes[1], 'description': room_attributes[2]})

        return rooms

    async def post(self, msg, room):

        self._transport.write('/post {}&{}$'.format(room.strip(), msg.strip()).encode('utf-8'))

    async def createroom(self, room_title, lname, description):
        self._transport.write('/make {}&{}&{}$'.format(room_title, lname, description).encode('utf-8'))
        create_room_response = await self._protocol._responses_q.get()
        message = create_room_response.rstrip('$')
        return message

    async def enterroom(self, choice):
        self._transport.write('/join {}$'.format(choice).encode('utf-8'))
        join_room_response = await self._protocol._responses_q.get()
        message = join_room_response.rstrip('$')
        return message

    async def exitroom(self, lname):
        self._transport.write('/leave {}$'.format(lname).encode('utf-8'))
        leave_room_response = await self._protocol._responses_q.get()
        return leave_room_response

    async def direct_message(self, lname, select, direct_message):
        self._transport.write('/direct {}&{}&{}$'.format(lname, select, direct_message).encode('utf-8'))
        direct_message_response = await self._protocol._responses_q.get()
        return direct_message_response

    async def get_user_msg(self):
        return await self._protocol._user_messages_q.get()

    async def list_direct_msg(self, auth_obj):
        url = "https://api.twitter.com/1.1/direct_messages/events/list.json"

        response = requests.get(url, auth=auth_obj)
        response.raise_for_status()
        r_json = json.loads(response.text)
        print(r_json)
        messages = [(e['id'], e['message_create']['message_data']['text']) for e in r_json['events']]
        return messages

    async def send_direct_msg(self, auth_obj):
        url = "https://api.twitter.com/1.1/direct_messages/events/new.json"
        payload = {"event":
                       {"type": "message_create",
                        "message_create":
                            {"target": {"recipient_id": "1070030057442369537"},
                             "message_data": {"text": "Just wanted to say hi!"}
                             }
                        }
                   }

        response = requests.post(url, data=json.dumps(payload), auth=auth_obj)
        response.raise_for_status()
        return json.loads(response.text)

    async def get_followers(self, auth_obj):
        url = "https://api.twitter.com/1.1/followers/list.json"
        response = requests.get(url=url, auth=auth_obj)
        response.raise_for_status()
        r_json = json.loads(response.text)
        dm_msg = [(r['screen_name'], r['name']) for r in r_json['users']]
        return dm_msg

if __name__ == '__main__':
    LOCAL_HOST = '127.0.0.1'
    PORT = 8080

    loop = asyncio.get_event_loop()
    chat_client = ChatClient(LOCAL_HOST, PORT)
    asyncio.ensure_future(chat_client._connect())

    chat_client.disconnect()
