from src.sock import Sock
from src.utils.parser import Parser
from threading import Thread


class Sender(Thread):
    dest_addr = None  # Tuple[str, int]

    def __init__(self, sock: Sock, parser: Parser):
        Thread.__init__(self, name='Sender', daemon=True)
        self.sockint = sock
        self.socket = sock.get_socket()
        self.parser = parser

    def send(self, dgram):
        self.socket.sendto(dgram, self.dest_addr)

    # ------------------------------------------------ #
    # two-way handshake

    def send_syn(self):
        dest_addr = input('> connect to (IP): ')
        dest_port = input('> at port: ')
        self.dest_addr = (dest_addr, int(dest_port))

        flag = 0
        dgram = self.parser.create_dgram(flag, 0, 0, '')
        self.send(dgram)

    def send_ack(self):
        flag = 1
        dgram = self.parser.create_dgram(flag, 0, 0, '')
        self.send(dgram)

    # ------------------------------------------------ #
    #   MSG

    def send_message(self):
        data = input('# ')

        info_syn, batch_list = self.parser.create_batch(3, data)
        self.send(info_syn)

        # msg in multiple batches
        if isinstance(batch_list[0], list):
            for batch in batch_list:
                for dgram in batch:
                    self.send(dgram)
                # TODO waiting for ACK before another batch

        # msg in single batch
        elif isinstance(batch_list, list):
            for dgram in batch_list:
                self.send(dgram)

        # msg in single dgram
        elif isinstance(batch_list, bytes):
            self.send(batch_list)

        else:
            print('Unknown type ', type(batch_list))
            print(batch_list)

    def send_msg_ack(self, batch_no):
        dgram = self.parser.create_dgram(5, batch_no, 0, '')
        self.send(dgram)