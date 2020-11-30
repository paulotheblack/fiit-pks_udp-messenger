from src.sock import Sock
from src.utils.parser import Parser
from src.sender import Sender


class Cli:

    def __init__(self, sockint: Sock, parser: Parser, sender: Sender):
        self.sockint = sockint
        self.socket = sockint.get_socket()
        self.parser = parser
        self.sender = sender

    def welcome(self):
        print(
            f'\t\tWelcome!\n'
            f'type ":c" to establish connection\n'
            f'type ":m" to send message\n'
            f'type ":f" to send file\n'
            f'type ":s" to change settings\n'
            f'type ":q" to exit program\n'
            f'Your address is set to: {self.socket.getsockname()}\n'
        )

    def stdin(self):
        self.welcome()

        while True:
            action = input('')

            if action == ':c':  # establish connection
                self.sender.send_syn()

            elif action == ':m':  # send message
                self.sender.send_data()

            elif action == ':f':  # send file
                self.sender.send_data(file=True)

            elif action == ':d':  # drop connection [do not send keep-alive]
                pass

            elif action == ':s':  # settings for changing dgram size
                self.parser.get_info()
                self.parser.set_dgram_size()

            elif action == ':q':  # quit program
                self.sockint.close_socket()
                print('Auf viedersehen!')
                exit(0)
            else:
                print('$ Unknown action, please try again')
