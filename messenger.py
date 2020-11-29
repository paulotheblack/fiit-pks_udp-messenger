from src.sock import Sock
from src.utils.parser import Parser
from src.sender import Sender
from src.listener import Listener
from src.utils.cli import Cli


def main():
    parser = Parser()

    args = parser.parse_args()
    local_ip = args['a']
    local_port = args['p']

    socket = Sock(local_ip, local_port)

    sender = Sender(socket, parser)
    sender.start()
    listener = Listener(socket, parser, sender)
    listener.start()

    cmd = Cli(socket, parser, sender)
    cmd.stdin()


if __name__ == '__main__':
    main()
