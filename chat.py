import sys
import aioconsole
import asyncio
import click
import requests
import requests_oauthlib
from server.chat_server import ChatServer
from client.chat_client import (
    ChatClient,
    NotConnectedError,
    LoginConflictError,
    LoginError,
    CreationError,
    CreateConflictError
)

async def display_msgs(chat_client):
    while True:
        msg = await chat_client.get_user_msg()
        print('\n\n\t\tRecieved Message: {}'.format(msg))

async def handle_user_input(chat_client, loop):
    uname = False
    lname = ''
    enter_room = ''
    rooms = []
    auth_obj = init_auth()
    while True:
        print('\n')
        print('< 1 > Close the connection and quit.')
        print('< 2 > List the logged in users.')
        print('< 3 > Login.')
        print('< 4 > List the rooms.')
        print('< 5 > Post messages to a room.')
        print('< 6 > Create a new private room.')
        print('< 7 > Join a room.')
        print('< 8 > Leave a room.')
        print('< 9 > Send a direct message.')
        print('< T1 > List direct messages from twitter.')
        print('< T2 > List twitter followers.')
        print('< T3 > Send a direct message.')

        print('\tchoice: ', end='', flush=True)

        command = await aioconsole.ainput()
        if command == '1':
            # disconnect
            try:
                chat_client.disconnect()
                print('Disconnected.')
                loop.stop()
            except NotConnectedError:
                print('Client is not connected ...')
            except Exception as e:
                print('Error disconnecting {}'.format(e))

        elif command == '2':  # list registered users
            users = await chat_client.lru()
            print('Logged-in users: {}'.format(', '.join(users)))

        elif command == '3':
            login_name = await aioconsole.ainput('Enter login-name: ')
            try:
                await chat_client.login(login_name)
                uname = True
                lname = login_name
                print(f'Logged-in as {login_name}')

            except LoginConflictError:
                print('Login name already exists, please pick another name.')
            except LoginError:
                print('Error loggining in, try again.')

        elif command == '4':
            try:
                rooms = await chat_client.lrooms()
                for room in rooms:
                    print('\n\t\tName of Room ({}), Owner ({}): {}'.format(room['name'], room['owner'], room['description']))

            except Exception as e:
                print('We could not get the rooms you wanted from {}'.format(e))

        elif command == '5':
            try:

                client_message = await aioconsole.ainput('enter your message: ')
                await chat_client.post(client_message, enter_room)

            except Exception as e:
                print('There was an error posting a message {}'.format(e))

        elif command == '6':
            if uname:
                room_title = await aioconsole.ainput('Enter the name of the private room you want to enter: ')
                description = await aioconsole.ainput('Please give the room description: ')
                try:
                    select_response = await chat_client.createroom(room_title, lname, description)
                    print(select_response)

                except Exception as e:
                    print('There was an error creating your room {}'.format(e))
            else:
                print('You are not logged in. Log-in first to create a room!')

        elif command == '7':
            if uname:
                rooms = await chat_client.lrooms()
                for room in rooms:
                    print('\n\t\tName of Room ({})'.format(room['name']))
                choice = await aioconsole.ainput('\nChoose a room to enter: ')
                try:
                    link_reply = await chat_client.enterroom(choice)
                    enter_room = choice
                    print(link_reply)

                except Exception as e:
                    print('There was an error joining the room {}'.format(e))
            else:
                print('Error, you must be logged-in to join a room!')

        elif command == '8':
            if uname:
                try:
                    exit_response = await chat_client.exitroom(lname)
                    print(exit_response)

                except Exception as e:
                    print('There was a problem exiting the room {}'.format(e))
            else:
                print('You are not logged in or connected to a room.')

        elif command == '9':
            if uname:
                try:
                    users = await chat_client.lru()
                    print('\nThe logged-in users are: {}'.format(', '.join(users)))
                    select = await aioconsole.ainput('\nChoose a user to send a message to: ')
                    direct_message = await aioconsole.ainput('\nPlease enter a message to send: ')
                    direct_message_reply = await chat_client.direct_message(lname, select, direct_message)
                    print(direct_message_reply)

                except Exception as e:
                    print('There was an error sending the message {}'.format(e))
            else:
                print('Message could not send. Please log-in to send a message.')

        # Twitter options
        elif command == 'T1':
            if uname:
                try:
                    printOut = await chat_client.list_direct_msg(auth_obj)
                    print(printOut)

                except Exception as e:
                    print('Something went wrong.')
            else:
                print("You need to input a username.")

        elif command == 'T2':
            if uname:
                try:
                    printOut = await chat_client.get_followers(auth_obj)
                    print(printOut)

                except Exception as e:
                    print('Something went wrong.')
            else:
                print("You need a username!")

        elif command == 'T3':
            if uname:
                try:
                    dm_msg = await aioconsole.ainput('Please type your message: ')
                    printOut = await chat_client.send_direct_msg(auth_obj, dm_msg)
                    print(printOut)
                except Exception as e:
                    print('This is unfortunate. Something went wrong.')
            else:
                print("You need a username!")


@click.group()
def cli():
    pass

@cli.command(help="run chat client")
@click.argument("host")
@click.argument("port", type=int)
def connect(host, port):
    chat_client = ChatClient(ip=host, port=port)
    loop = asyncio.get_event_loop()

    loop.run_until_complete(chat_client._connect())


    asyncio.ensure_future(handle_user_input(chat_client=chat_client, loop=loop))
    asyncio.ensure_future(display_msgs(chat_client=chat_client))

    loop.run_forever()

@cli.command(help='run chat server')
@click.argument('port', type=int)
def listen(port):
    click.echo('starting chat server at {}'.format(port))
    chat_server = ChatServer(port=port)
    chat_server.start()

def verify_credentials(auth_obj):
    url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
    response = requests.get(url, auth=auth_obj)
    return response.status_code == 200


def init_auth():
    consumer_key = 'QcLsbH5EikUk3wrEe4CQ6CAmH'
    consumer_secret = 'zDn1YwFPbKrBFNkAYEQ0EEsgrlEd4Yor5bz2MXhh32VG5Gshgx'
    access_token = '1056970108596314113-Kbbn2ufTYoVGSDyLjEEI7ovVMYWxtT'
    access_secret = 'T8nYdvbnvQ5Av5YWptMZw7rdfF02MyNyA72KRgfs9IaSU'
    auth_obj = requests_oauthlib.OAuth1(consumer_key,
                                        consumer_secret,
                                        access_token,
                                        access_secret)

    if verify_credentials(auth_obj):
        print('Your credentials have been validated!')
        return auth_obj
    else:
        print('Your credentials have not been validated.')

if __name__ == '__main__':
    cli()
