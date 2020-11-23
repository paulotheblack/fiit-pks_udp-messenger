from src.sock import Sock
from src.sender import Sender


def main():
    socket = Sock()

    sender = Sender(socket.get_socket())


if __name__ == '__main__':
    main()
