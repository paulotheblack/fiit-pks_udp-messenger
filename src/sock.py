from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, gethostname


class Sock:
    local_ip: str
    local_port: str
    local_address: tuple
    _sock: socket

    def __init__(self):
        self.create_socket()

    def create_socket(self, address='127.0.0.1', port=42040):
        self.local_ip = address
        self.local_port = port
        self.local_address = (self.local_ip, self.local_port)
        self._sock = socket(AF_INET, SOCK_DGRAM)
        try:
            self._sock.bind(self.local_address)
        except PermissionError:
            print('>> Selected port is occupied!')
            self.local_port = int(input('$ at port: '))

    def get_socket(self):
        return self._sock

    def close_socket(self, msg='Socket have been closed'):
        print(msg)
        self._sock.close()

    def set_locale(self):
        address = input('$ Local IP address (localhost): ')
        port = int(input('$ at port: '))

        self.close_socket(msg='Closing previously created socket.')
        self.create_socket(address, port)
