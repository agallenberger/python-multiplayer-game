## =================================================================================================
## Python 3.6+
## =================================================================================================
import json
import socket
import sys
import threading
import time

import player
import pysockets

## =================================================================================================

PLAYERS = {}

## =================================================================================================
def main():
    ## Get device local IP
    ip = pysockets.get_ip()

    ## Create TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ## Avoid port conflict
    port = pysockets.PORT
    while True:
        try:
            s.bind((ip, port))
            print (f'Server socket bound to {ip}:{port}')
            break
        except OSError:
            port += 1
            if port > 65535:
                port = 0

    ## Put the socket into listening mode
    s.listen(5)

    ## Accept connections
    try:
        while True:
            ## Establish connection with client
            c, addr = s.accept()
            print(f'Got connection from {addr[0]}:{addr[1]}')

            ## Host the connection in its own thread
            thr = threading.Thread(target=read_data_thread_function, args=(OnlinePlayer(c, addr),))
            thr.start()
            time.sleep(0.2)

    except KeyboardInterrupt:
        for op in PLAYERS.values():
            op.c.close()

        s.shutdown(socket.SHUT_RDWR)
        s.close()


## -------------------------------------------------------------------------------------------------
def json_dumps_players():
    '''
    Get PLAYERS as JSON string

    :return: string
    '''
    json_data = {'players': []}
    for op in PLAYERS.values():
        if op.player_data is not None:
            json_data['players'].append(op.as_dict())

    return json.dumps(json_data)


## -------------------------------------------------------------------------------------------------
def read_data_thread_function(online_player):
    '''
    Reads data from a particular connection. Each connection will have its own instance of this
    function in a unique thread.

    :param online_player: OnlinePlayer
    :return: None
    '''
    while True:
        ## Read player data
        try:
            msg = pysockets.receive_msg(online_player.c)
            online_player.player_data = player.player_from_json(msg)

        except json.JSONDecodeError:
            continue

        except ConnectionResetError:
            try:
                print(f'Player #{online_player.player_data.id} disconnected (ConnectionResetError)')
                del PLAYERS[online_player.player_data.id]
            except AttributeError:
                print(f'{online_player.addr[0]}:{online_player.addr[1]} disconnected '
                      f'(ConnectionResetError)')

            broadcast_player_info()
            return

        ## Update player info if its in-game, otherwise delete the player
        if online_player.player_data.in_game == True:
            PLAYERS[online_player.player_data.id] = online_player
            broadcast_player_info()
        else:
            print(f'Player #{online_player.player_data.id} disconnected')
            del PLAYERS[online_player.player_data.id]
            broadcast_player_info()
            return


## -------------------------------------------------------------------------------------------------
def broadcast_player_info():
    '''
    Broadcast player data to all connections

    :return: None
    '''
    try:
        ## Broadcast updated player data back to clients
        json_data = json_dumps_players()

        for p in list(PLAYERS.values()):
            pysockets.send_msg(p.c, json_data)

    except (ConnectionResetError, ConnectionAbortedError):
        pass


## -------------------------------------------------------------------------------------------------
class OnlinePlayer:
    def __init__(self, connection, address):
        '''
        Class to correlate player data with a particular connection

        :param connection: TCP connection obj
        :param address: TCP address
        '''
        self.c = connection
        self.player_data = None
        self.addr = address


    def __repr__(self):
        return repr(self.player_data)


    def as_dict(self):
        if self.player_data is not None:
            return self.player_data.as_dict()
        else:
            return {}


## =================================================================================================
if __name__ == '__main__':
    assert sys.version_info >= (3, 6)
    main()
