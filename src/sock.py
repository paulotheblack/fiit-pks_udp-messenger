from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, gethostname


class Sock:
    local_ip: str
    local_port: str
    local_address: tuple
    _sock: socket

    def __init__(self, ip, port):
        self.local_ip = ip
        self.local_port = port
        self.local_address = (ip, port)
        self.create_socket(ip, port)

    def create_socket(self, address, port):
        """
            create and bind socket (UDP)

            args:
                address: str    IP_ADDRESS (IPv4)
                port: int       PORT

            return: void
        """
        self.local_ip = address
        self.local_port = int(port)
        self.local_address = (self.local_ip, self.local_port)
        self._sock = socket(AF_INET, SOCK_DGRAM)

        try:
            self._sock.bind(self.local_address)
        except PermissionError:
            print('>> Selected port is occupied!')
            self.local_port = int(input('$ at port: '))

    def get_socket(self):
        return self._sock

    def close_socket(self):
        self._sock.close()
        self._sock = None
        print('Socket have been closed')

    def close_socket_stop(self):
        self._sock.close()
        print('Socket have been closed\nAuf viedersehen!')
        exit(0)
