from src.sock import Sock
from src.sender import Sender


def main():
    socket = Sock()

    sender = Sender(socket)
    sender.run()


if __name__ == '__main__':
    main()
