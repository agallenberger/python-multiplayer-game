## =================================================================================================
## Python 3.6+
## =================================================================================================
import json
import os
import socket
import sys
import threading
import time
import tkinter

import constants
import player
import pysockets

## =================================================================================================
def main():
    game = GuiGame()
    game.run()


## -------------------------------------------------------------------------------------------------
class GuiGame:
    def __init__(self, title=f'SOE Game ({os.getpid()})'):
        '''
        Game GUI class

        :param title: window title
        '''
        ## To be initialized when game is started
        self.in_game = False
        self.player  = None
        self.canvas  = None

        ## Create window
        self.root = tkinter.Tk()
        self.root.title(title)
        self.root.geometry(constants.WINDOW_SIZE_XY)
        self.label = tkinter.Label(self.root, text='Press enter to start', font=('Helvetica', 12))

        ## Create entry box for server address
        self.entry_label = tkinter.Label(self.root, text='Enter server address:',
            font=('Helvetica', 12))
        self.server_addr = tkinter.StringVar()
        self.server_addr.set(f'{pysockets.get_ip()}:{pysockets.PORT}')
        self.entry_addr = tkinter.Entry(self.root, textvariable=self.server_addr,
            font=('Helvetica', 12), justify=tkinter.CENTER)
        self.entry_label.pack()
        self.entry_addr.pack()
        self.label.pack()

        ## Bind movement keys
        self.root.bind('<Return>', self.start_game)
        self.root.bind('<Left>', self.move_left)
        self.root.bind('<Right>', self.move_right)
        self.root.bind('<Up>', self.move_up)
        self.root.bind('<Down>', self.move_down)

        ## Start online TCP service in daemon thread
        self.mp_connected   = False
        self.mp_players     = []
        self.mp_player_dots = []
        self.server         = None
        self.stop_thread    = False
        self.online_thread  = threading.Thread(target=self.online_function, daemon=True)
        self.connect_thread = threading.Thread(target=self.server_connect, daemon=True)

    def run(self):
        '''
        Runs the GUI process

        :return: None
        '''
        ## Bind X to function for safe shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        ## Start GUI
        self.root.focus_set()
        self.root.mainloop()


    def start_game(self, event):
        '''
        Starts the game

        :param event:
        :return: None
        '''
        ## Start TCP thread
        if self.mp_connected == False:
            self.server_connect()

        if self.mp_connected == True:
            ## Start server communication
            try:
                self.online_thread.start()
            except RuntimeError:
                pass

            ## Place player in game
            if self.in_game == False:
                ## Create player
                self.player = player.Player(id=int(time.time()*1000), in_game=True)

                ## Send player info to server
                pysockets.send_msg(self.server, self.player.as_json())

                ## Redraw label to reflect player number and color
                self.label.config(fg=self.player.color, text=f'You are player '
                                  f'{self.player.id + 1}. Use arrow keys to move.')
                self.canvas = tkinter.Canvas(self.root, bg='white', height=constants.CANVAS_SIZE_Y,
                                             width=constants.CANVAS_SIZE_X)
                self.canvas.pack()

                ## Draw player on canvas
                n = constants.DOT_SIZE / 2
                self.dot = self.canvas.create_oval((self.player.x - n), (self.player.y - n),
                                                   (self.player.x + n), (self.player.y + n),
                                                   fill=self.player.color)
                self.in_game = True
                self.update_game_loop()
        else:
            self.label.config(text='Server not found. Run server and check address, then press '
                              'enter to start')


    def move_left(self, event):
        '''
        Move the player left

        :param event: tkinter event
        :return: None
        '''
        if self.in_game == True:
            if self.player.x - constants.MOVE_SIZE > 0 + constants.DOT_SIZE/2:
                self.player.x = self.player.x - constants.MOVE_SIZE
                self.move(-constants.MOVE_SIZE, 0)


    def move_right(self, event):
        '''
        Move the player right

        :param event: tkinter event
        :return: None
        '''
        if self.in_game == True:
            if self.player.x + constants.MOVE_SIZE < constants.CANVAS_SIZE_X - constants.DOT_SIZE/2:
                self.player.x = self.player.x + constants.MOVE_SIZE
                self.move(constants.MOVE_SIZE, 0)


    def move_up(self, event):
        '''
        Move the player up

        :param event: tkinter event
        :return: None
        '''
        if self.in_game == True:
            if self.player.y - constants.MOVE_SIZE > constants.DOT_SIZE/2:
                self.player.y = self.player.y - constants.MOVE_SIZE
                self.move(0, -constants.MOVE_SIZE)


    def move_down(self, event):
        '''
        Move the player down

        :param event: tkinter event
        :return: None
        '''
        if self.in_game == True:
            if self.player.y + constants.MOVE_SIZE < constants.CANVAS_SIZE_Y - constants.DOT_SIZE/2:
                self.player.y = self.player.y + constants.MOVE_SIZE
                self.move(0, constants.MOVE_SIZE)


    def move(self, dx, dy):
        '''
        Move the player dot & send updated position to server

        :param dx: delta x movement
        :param dy: delta y movement
        :return: None
        '''
        ## Move the player dot
        self.canvas.move(self.dot, dx, dy)

        ## Send my player info to server
        if self.mp_connected == True:
            try:
                pysockets.send_msg(self.server, self.player.as_json())
            except OSError:
                pass

            if self.in_game:
                self.label.config(text=f'You are player {self.player.id + 1}. Use arrow keys to '
                                       f'move.')


    def update_game_loop(self):
        '''
        Update the game window & positions of online players. This function calls itself.

        :return: None
        '''
        ## Delete old player dots
        for p_dot in self.mp_player_dots:
            self.canvas.delete(p_dot)

        ## Update player information from server
        self.mp_player_dots = []
        n = constants.DOT_SIZE / 2
        for p in self.mp_players:
            if p.id == self.player.id:
                continue

            ## Draw updated player dots
            if p.in_game == True:
                self.mp_player_dots.append(
                    self.canvas.create_oval((p.x - n), (p.y - n), (p.x + n), (p.y + n),
                        fill=p.color)
                )

        self.canvas.after(50, self.update_game_loop)


    def on_closing(self):
        '''
        Shut down the game properly when red X is clicked

        :return: None
        '''
        ## Remove player from game & update server
        if self.player is not None:
            self.player.in_game = False
            pysockets.send_msg(self.server, self.player.as_json())

        ## Close TCP connection
        self.stop_thread = True

        ## Close window
        self.root.destroy()


    def server_connect(self):
        '''
        Connect to multiplayer server

        :return: None
        '''
        ## Create socket
        self.server = socket.socket()

        ## Connect to server
        try:
            if pysockets.is_valid_address(self.server_addr.get()) == True:
                ip, port = self.server_addr.get().split(':')
                try:
                    self.server.connect((ip, int(port)))
                except OSError:
                    self.entry_label.config(text='Could not connect to server address:')
                    return

                print(f'Connected to server: {ip}:{port}')
                self.entry_label.config(text='Connected to:')
                self.entry_addr.config(state=tkinter.DISABLED)
                self.mp_connected = True
            else:
                self.entry_label.config(text='Invalid server address:')

        except ConnectionRefusedError:
            pass


    def online_function(self):
        '''
        Sync player with online players (Run in its own thread)

        :return: None
        '''
        ## Receive messages
        try:
            while self.stop_thread == False and self.mp_connected == True:
                try:
                    msg = json.loads(pysockets.receive_msg(self.server))

                    ## Update player list
                    temp_player_list = []
                    for p in msg['players']:
                        temp_player_list.append(player.player_from_dict(p))

                    self.mp_players = temp_player_list

                except json.JSONDecodeError:
                    pass

        except ConnectionResetError:
            self.label.config(text='Disconnected from server (ConnectionResetError)')
            self.restart_online_service()

        except OSError:
            self.label.config(text='Disconnected from server (OSError)')
            self.restart_online_service()

        if self.mp_connected == False:
            print('reconnect')
            self.server_connect()
            self.online_function()


    def restart_online_service(self):
        self.entry_label.config(text='Disconnected from:')
        self.server.close()
        self.mp_connected = False
        self.mp_players = []
        self.connect_thread.start()
        self.server_connect()
        self.online_function()


## =================================================================================================
if __name__ == '__main__':
    assert sys.version_info >= (3, 6)
    main()
