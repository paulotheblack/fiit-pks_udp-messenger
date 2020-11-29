from src.sock import Sock
from src.utils.parser import Parser
from src.sender import Sender

from threading import Thread


class Listener(Thread):
    source_address: tuple = None

    CURRENT_BATCH = None
    CURRENT_DGRAM = None

    LAST_BATCH_INDEX = None
    LAST_DGRAM_INDEX = None

    DATA = ''

    def __init__(self, socket: Sock, parser: Parser, sender: Sender):
        Thread.__init__(self, name='Listener', daemon=True)
        self.sockint = socket
        self.socket = socket.get_socket()
        self.parser = parser
        self.sender = sender

    def run(self):
        while True:
            dgram, self.source_address = self.socket.recvfrom(1500)

            header = self.parser.get_header(dgram)
            data = self.parser.get_data(dgram)

            if header[0] == 0:  # SYN
                self.sender.dest_addr = self.source_address
                self.got_syn()
                self.sender.send_ack()

            elif header[0] == 1:  # ACK
                self.got_ack()

            elif header[0] == 2:   # REQ
                self.got_req(header, data)

            elif header[0] == 3:  # MSG
                self.got_message(header, data)

            elif header[0] == 4:  # FILE
                pass
            elif header[0] == 5:  # ACK_MSG
                self.got_ack_msg(header)

            elif header[0] == 6:  # ACK_FILE
                pass
            elif header[0] == 7:  # NACK
                pass

    # two-way handshake 'C_SYN'
    def got_syn(self):
        print(f'\n[SYN] from: {self.source_address[0]}:{self.source_address[1]}')

    # two-way handshake 'C_SYN'
    def got_ack(self):
        print(f'[ACK] from {self.source_address[0]}:{self.source_address[1]}')

    def got_req(self, header, data):
        self.DATA = ''
        self.LAST_BATCH_INDEX = header[1]
        self.LAST_DGRAM_INDEX = header[2]
        print(f'[REQ] last_batch: {self.LAST_BATCH_INDEX}, last_dgram: {self.LAST_DGRAM_INDEX}, type: {data.decode()}')

    @staticmethod
    def got_ack_msg(header):
        print(f'[ACK_MSG] {header[1]}')

    def got_message(self, header, data: bytes):
        self.CURRENT_BATCH = header[1]
        self.CURRENT_DGRAM = header[2]

        # message in single datagram
        if self.LAST_BATCH_INDEX == 0 and self.LAST_DGRAM_INDEX == 0:
            print(f'[{self.source_address[1]}] {data.decode()}')
            self.sender.send_msg_ack(self.CURRENT_BATCH)
            return

        # message in single batch
        elif self.LAST_BATCH_INDEX == 0:
            self.DATA += data.decode()

        # message in multiple batches
        else:
            self.DATA += data.decode()
            # each batch -> send_ack
            if self.CURRENT_DGRAM == self.parser.BATCH_SIZE - 1:
                self.sender.send_msg_ack(self.CURRENT_BATCH)

        # message in single batch -> print message && send_ack
        if self.LAST_BATCH_INDEX == 0 and self.CURRENT_BATCH == 0 and self.LAST_DGRAM_INDEX == header[2]:
            print(f'[{self.source_address[1]}]: {self.DATA}')
            self.sender.send_msg_ack(self.CURRENT_BATCH)

        # message in multiple batches -> print message && send_last_ack
        elif self.LAST_BATCH_INDEX == header[1] and self.LAST_DGRAM_INDEX == header[2]:
            print(f'[{self.source_address[1]}]: {self.DATA}')
            self.sender.send_msg_ack(self.CURRENT_BATCH)
