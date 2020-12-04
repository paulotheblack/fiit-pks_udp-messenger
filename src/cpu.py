import select

from src.utils.parser import Parser
from src.sender import Sender
from src.sock import Sock

import src.utils.color as c


class Cpu:
    SRC_ADDR: tuple = None

    RECV_DATA_BUFFER: list = []

    CURR_BATCH_INDEX: int = None
    CURR_DGRAM_INDEX: int = None
    LAST_BATCH_INDEX: int = None
    LAST_DGRAM_INDEX: int = None
    DGRAMS_RECV: int = 0

    IS_FILE: bool = None
    FILE_NAME: str = None
    FILE_PATH: str = None

    CONNECTED: bool = None

    def __init__(self, socket: Sock, parser: Parser, sender: Sender):
        self.sockint = socket
        self.socket = socket.get_socket()
        self.pars = parser
        self.sender = sender
        self.FILE_PATH = self.pars.get_args()['f']

    # -------------------  HANDSHAKE ------------------------- #
    def recv_syn(self, source_address: tuple):
        self.SRC_ADDR = source_address
        self.sender.DEST_ADDR = source_address
        self.sender.send_ack()
        self.sender.CONNECTED = True
        print(f'{c.RED + "[log]" + c.DARKCYAN} {source_address[0]}{c.END} connected to session!')

    def recv_ack(self, source_address: tuple):
        self.SRC_ADDR = source_address
        self.sender.CONNECTED = True
        self.CONNECTED = True

        print(f'{c.RED + "[log]" + c.END} Connection with {c.DARKCYAN}{self.SRC_ADDR[0]}{c.END} established!')

    def recv_fin(self):
        print(f'{c.PURPLE + c.BOLD}[{self.SRC_ADDR[0]}] Closed connection!{c.END}')
        self.sender.CONNECTED = False
        self.sender.DEST_ADDR = None
        self.SRC_ADDR = None

    # -------------------  ACKs/NACK ------------------------- #
    def recv_request(self, header, data):
        self.LAST_BATCH_INDEX = header[1]
        self.LAST_DGRAM_INDEX = header[2]

        self.RECV_DATA_BUFFER = self.pars.create_data_buffer(self.LAST_BATCH_INDEX, self.LAST_DGRAM_INDEX)
        # FILE
        if data.decode() == '4':
            self.IS_FILE = True
            print(f'{c.DARKCYAN}[{self.SRC_ADDR[0]}]{c.RED + c.BOLD} is sending file "{self.FILE_NAME}"{c.END}')
        # MSG
        else:
            self.IS_FILE = False

    def recv_ack_data(self, header):
        self.sender.GOT_ACK = True
        self.sender.ACK_NO = header[1]
        # print(f'[log] recv ACK')

    def recv_nack(self, header):
        self.sender.GOT_NACK = True
        self.sender.TO_RESEND = self.pars.parse_nack_field(header)

        # debug
        print(f'{c.RED}[RECV_NACK]{c.END} stderr in: {self.sender.TO_RESEND} dgram/s')

    # ---------------------  DATA ---------------------------- #
    def recv_data(self, header, data: bytearray, file_name=False):
        self.CURR_BATCH_INDEX = header[1]
        self.CURR_DGRAM_INDEX = header[2]

        self.DGRAMS_RECV += 1

        # Checksum is correct
        if self.pars.check_sum(header, data):
            self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX][self.CURR_DGRAM_INDEX] = data
        # if recv corrupted data
        else:
            self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX][self.CURR_DGRAM_INDEX] = None
            print(f'[!!!] -> [{self.CURR_BATCH_INDEX}][{self.CURR_DGRAM_INDEX}]')

        if not self.pars.find_index(self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX], lambda x: x == b''):
            to_resend = self.pars.find_index(self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX], lambda x: x is None)
            if not to_resend:
                # If okay, send ACK_DATA
                self.sender.send_ack_data(self.CURR_BATCH_INDEX)

                # If last batch process data:
                if self.CURR_BATCH_INDEX == self.LAST_BATCH_INDEX:
                    self.stdout(file_name=file_name)

            else:
                # If any missing data, send NACK
                self.sender.send_nack(to_resend)
                # Reset to_resend
                self.reset_batch(to_resend)
                to_resend.clear()

    def reset_batch(self, to_resend):
        for index, dgram in enumerate(self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX]):
            if index in to_resend:
                self.RECV_DATA_BUFFER[self.CURR_BATCH_INDEX][index] = b''

    def stdout(self, file_name=False):
        # If file
        if self.IS_FILE:
            # save file
            path, size = self.pars.write_file(self.FILE_PATH, self.FILE_NAME, self.RECV_DATA_BUFFER)
            # STDOUT PRINT
            if size:
                print(f'{c.DARKCYAN}[FILE]({size})({self.DGRAMS_RECV}DGs) {c.RED + c.BOLD}"{path}"{c.END}')
            # IF SIZE == 0: OSError (Permissions)
            else:
                print(f'> ({self.DGRAMS_RECV} DR) Unable to save file to: {self.FILE_PATH}')
            # reset DGs counter
            self.DGRAMS_RECV = 0

        # If file name
        elif file_name:
            # merge and assign file name
            self.FILE_NAME = self.pars.process_message(self.RECV_DATA_BUFFER)

        # if message
        else:
            msg = self.pars.process_message(self.RECV_DATA_BUFFER)
            # STDOUT PRINT
            print(f'{c.DARKCYAN}[{self.SRC_ADDR[0]}]{c.END}'
                  f'({len(msg)}B)({self.DGRAMS_RECV}DGs) '
                  f'{c.YELLOW + msg + c.END}')
            # reset DGs counter
            self.DGRAMS_RECV = 0
