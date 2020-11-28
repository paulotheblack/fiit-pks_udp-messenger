from src.sock import Sock
from src.parser import Parser
from src.cli import Cli


def main():
    socket = Sock()
    sender = Parser(socket)
    cmd = Cli(sender, socket)

    cmd.run()


if __name__ == '__main__':
    main()
