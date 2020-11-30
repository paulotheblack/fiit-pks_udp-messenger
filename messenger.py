from src.sock import Sock
from src.utils.parser import Parser
from src.sender import Sender
from src.listener import Listener
from src.cpu import Cpu
from src.utils.cli import Cli


def messenger():
    # __init__ parser
    parser = Parser()

    # parse CLI args (ip_address, port)
    args = parser.parse_args()
    local_ip = args['a']
    local_port = args['p']

    # __init__ socket
    socket = Sock(local_ip, local_port)

    # __init__ thread for sending messages
    sender = Sender(socket, parser)
    sender.start()

    # __init__ CPU (contains logic)
    cpu = Cpu(socket, parser, sender)

    # __init__ thread for receiving messages
    listener = Listener(socket, parser, cpu)
    listener.start()

    # __init__ CLI user interface
    cli = Cli(socket, parser, sender)
    cli.stdin()


if __name__ == '__main__':
    messenger()
