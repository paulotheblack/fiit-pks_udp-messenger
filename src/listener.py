from threading import Thread

from src.sock import Sock
from src.utils.parser import Parser
from src.cpu import Cpu


class Listener(Thread):
    source_address: tuple = None

    CURRENT_BATCH = None
    CURRENT_DGRAM = None

    LAST_BATCH_INDEX = None
    LAST_DGRAM_INDEX = None
    IS_FILE = False

    BATCH: list
    DATA = ''

    def __init__(self, socket: Sock, parser: Parser, cpu: Cpu):
        Thread.__init__(self, name='Listener', daemon=True)
        self.socket = socket.get_socket()
        self.parser = parser
        self.cpu = cpu

    def run(self):
        while True:
            dgram, source_address = self.socket.recvfrom(1500)

            header = self.parser.get_header(dgram)
            data = self.parser.get_data(dgram)

            if header[0] == 0:  # SYN
                self.cpu.recv_syn(source_address)

            elif header[0] == 1:  # ACK
                self.cpu.recv_ack(source_address)

            elif header[0] == 2:   # REQ
                self.cpu.recv_request(header, data)

            elif header[0] == 3:  # MSG
                self.cpu.recv_data(header, data)

            elif header[0] == 4:  # FILE
                self.cpu.recv_data(header, data)

            elif header[0] == 5:  # ACK_MSG
                self.cpu.recv_ack_msg(header)

            elif header[0] == 6:  # ACK_FILE
                self.cpu.recv_ack_file(header)

            elif header[0] == 7:  # NACK
                self.cpu.recv_nack(header)

            elif header[0] == 8:  # KEEP_ALIVE
                pass

            elif header[0] == 9:  # FILE_NAME
                self.cpu.recv_data(header, data, file_name=True)
