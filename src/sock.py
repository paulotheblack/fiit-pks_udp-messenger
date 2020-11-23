from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, gethostname


class Sock:
    local_ip: str
    local_port: str
    local_address: tuple
    sock: socket

    def __init__(self):
        self.create_socket()

    def create_socket(self, address='127.0.0.1', port=42042):
        self.local_ip = address
        self.local_port = port
        self.local_address = (self.local_ip, self.local_port)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(self.local_address)
        # print(
        #     f'Socket created ==> '
        #     f'{self.sock.getsockname()}'
        # )

    def get_socket(self):
        return self.sock

    def close_socket(self):
        self.sock.close()
        print(f'> Socket have been closed')

    def update_locale(self, ip, port):
        # self.local_ip = gethostbyname(gethostname())
        self.local_address = (ip, port)
