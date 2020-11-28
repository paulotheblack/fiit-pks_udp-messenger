from src.sock import Sock
from src.parser import Parser


class Cli:

    def __init__(self, parser: Parser, sockint: Sock):
        self.parser = parser
        self.sockint = sockint
        self.socket = sockint.get_socket()
        # self.listener = listener

    def welcome(self):
        print(
            f'Welcome!\n'
            f'Your address is set to: {self.socket.getsockname()}\n'
            f'type ":c" to establish connection\n'
            f'then you can ":m" send message or ":f" send file'
        )

    def run(self):
        self.welcome()

        while True:
            action = input('$ ')

            if action == ':c':  # establish connection
                self.parser.send_syn()
            elif action == ':m':  # send message
                self.parser.send_message()
            elif action == ':f':  # send file
                pass
            elif action == ':d':  # drop connection [do not send keep-alive]
                pass
            elif action == ':s':  # settings for changing port and dgram size
                self.parser.get_info()
                self.parser.set_dgram()
                self.sockint.set_locale()
            elif action == ':q':  # quit program
                self.sockint.close_socket()
                print('Auf viedersehen!')
                exit(0)
            else:
                print('! Unknown action, please try again')
