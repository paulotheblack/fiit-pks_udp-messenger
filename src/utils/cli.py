from src.sock import Sock
from src.utils.parser import Parser
from src.sender import Sender
from src.keepalive import KeepAlive


class Cli:

    def __init__(self, sockint: Sock, parser: Parser, sender: Sender, keepalive: KeepAlive):
        self.sockint = sockint
        self.socket = sockint.get_socket()
        self.parser = parser
        self.sender = sender
        self.keepalive = keepalive

    def welcome(self):
        print(
            f'\t\tWelcome!\n'
            f'":c" to establish connection\n'
            f'":m" to send message\n'
            f'":f" to send file\n'
            f'":s" to change settings\n'
            f'":q" to exit program\n'
            f'Your address is set to: {self.socket.getsockname()[0]}:{self.socket.getsockname()[1]}\n'
        )

    def stdin(self):
        self.welcome()

        while True:
            action = input('')

            if action == ':c':  # establish connection
                self.sender.send_syn()

            elif action == ':m':  # send message
                self.sender.input_data()

            elif action == ':f':  # send file
                self.sender.input_data(file=True)

            elif action == ':em':  # ARQ Message
                self.sender.input_data(err=True)

            elif action == ':ef':  # ARQ File
                self.sender.input_data(file=True, err=True)

            elif action == ':d':  # disconnect
                self.sender.send_fin()

            elif action == ':s':  # settings for changing dgram size
                self.parser.set_dgram_size()

            elif action == ':kk':
                self.keepalive.STOP = True
                print('> Stopped sending KeepAlive')

            elif action == ':q':  # quit program
                self.keepalive.STOP = True
                self.keepalive.KILL = True
                self.keepalive.join()
                # self.keepalive.
                self.sender.send_fin()
                self.sockint.close_socket_stop()

            else:
                print('> Unknown action, please try again')
