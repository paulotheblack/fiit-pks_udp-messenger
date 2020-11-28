from src.sock import Sock
from src.misc.parser import Parser
from src.sender import Sender
from src.misc.cli import Cli


def main():
    socket = Sock()
    parser = Parser(socket)
    sender = Sender(socket, parser)

    cmd = Cli(socket, parser, sender)
    cmd.run()


if __name__ == '__main__':
    main()
