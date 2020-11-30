from src.utils.parser import Parser
from src.sender import Sender
from src.sock import Sock

import src.utils.color as c


class Cpu:
    SRC_ADDR: tuple = None

    BATCH: list = []
    FULL_DATA: list = []

    CURR_BATCH_INDEX: int = None
    CURR_DGRAM_INDEX: int = None
    LAST_BATCH_INDEX: int = None
    LAST_DGRAM_INDEX: int = None

    IS_FILE: bool = None
    FILE_NAME: str = None
    FILE_PATH: str = None

    def __init__(self, socket: Sock, parser: Parser, sender: Sender):
        self.sockint = socket
        self.socket = socket.get_socket()
        self.pars = parser
        self.sender = sender

    # -------------------  HANDSHAKE ------------------------- #
    def recv_syn(self, source_address: tuple):
        self.SRC_ADDR = source_address
        self.sender.DEST_ADDR = source_address
        self.sender.send_ack()
        # debug
        print(f'\n[SYN] {source_address[0]}:{source_address[1]}')

    def recv_ack(self, source_address):
        self.SRC_ADDR = source_address
        self.sender.GOT_ACK = True
        # debug
        print(f'[ACK] {self.SRC_ADDR[0]}:{self.SRC_ADDR[1]}')

    # -------------------  ACKs/NACK ------------------------- #
    def recv_request(self, header, data):
        """
            TODO add docstring

            args:
            Runtime:
            return:
        """

        # Empty previous buffers
        if self.FULL_DATA:
            self.FULL_DATA.clear()
        if self.BATCH:
            self.BATCH.clear()

        self.LAST_BATCH_INDEX = header[1]
        self.LAST_DGRAM_INDEX = header[2]

        self.BATCH = self.pars.alloc_batch_array()
        # debug
        print(f'[REQ] last_batch: {self.LAST_BATCH_INDEX}, '
              f'last_dgram: {self.LAST_DGRAM_INDEX}, '
              f'is_file: {self.IS_FILE}')

        # If file, ask user for PATH to save it
        if data.decode() == 4:
            self.IS_FILE = True
            print(f'[{self.SRC_ADDR[1]}] Would like to send you file, please provide')
            self.FILE_PATH = input('$ Absolute path to save file: ')
        else:
            self.IS_FILE = False

    def recv_ack_msg(self, header):
        self.sender.GOT_ACK = True

        # debug
        print(f'[ACK_MSG] {header[1]}')

    def recv_ack_file(self, header):
        self.sender.GOT_ACK = True

        # debug
        print(f'[ACK_FILE] {header[1]}')

    # TODO maybe change logic of NACK
    def recv_nack(self, header):
        """
            Usage:
                1.
        """
        self.sender.GOT_NACK = True
        self.sender.TO_RESEND = self.pars.parse_nack_field(header)

        # debug
        print(f'[NACK] {self.sender.TO_RESEND}')

    # ---------------------  DATA ---------------------------- #
    def recv_data(self, header, data: bytearray):
        """
            TODO add docstring

            args:

            usage:

            return:
        """
        self.CURR_BATCH_INDEX = header[1]
        self.CURR_DGRAM_INDEX = header[2]

        # Checksum is correct
        if self.pars.check_checksum(header, data):

            # -  SINGLE DATAGRAM --------------------------------------------------- #
            if self.LAST_BATCH_INDEX == 0 and self.LAST_DGRAM_INDEX == 0:
                if self.IS_FILE:
                    self.sender.send_ack_file(self.CURR_BATCH_INDEX)
                    # TODO save file
                    pass
                else:
                    # send ACK
                    self.sender.send_ack_msg(self.CURR_BATCH_INDEX)
                    # CHAT PRINT
                    print(f'[{self.SRC_ADDR[1]}]({len(data)}B) {c.YELLOW + data.decode() + c.END}')

            # - SINGLE BATCH ------------------------------------------------------- #
            elif self.LAST_BATCH_INDEX == 0:
                # insert datagram to BATCH ta CURRENT INDEX
                self.BATCH[self.CURR_DGRAM_INDEX] = data

                # If last datagram
                if self.CURR_DGRAM_INDEX == self.LAST_DGRAM_INDEX:
                    # If no datagram is missing
                    if not self.pars.find_indices(self.BATCH, lambda x: x is None):
                        if self.IS_FILE:
                            self.sender.send_ack_file(self.CURR_BATCH_INDEX)
                            # TODO save file
                            pass
                        else:
                            # send ACK
                            self.sender.send_ack_msg(self.CURR_BATCH_INDEX)
                            # merge message
                            msg = self.pars.process_message(self.BATCH)
                            # CHAT PRINT
                            print(f'[{self.SRC_ADDR[1]}]({len(msg)}B) {c.YELLOW + msg + c.END}')
                    else:
                        self.sender.send_nack(self.BATCH)

            # - MULTIPLE BATCHES --------------------------------------------------- #
            else:
                # insert datagram to BATCH ta CURRENT INDEX
                self.BATCH[self.CURR_DGRAM_INDEX] = data

                # After each batch
                if self.CURR_DGRAM_INDEX == (self.pars.BATCH_SIZE - 1):
                    # if no datagram is missing
                    if not self.pars.find_indices(self.BATCH, lambda x: x is None):
                        # send ACK
                        self.sender.send_ack_msg(self.CURR_BATCH_INDEX)
                        # append FULL_DATA with current BATCH
                        self.FULL_DATA.append(self.BATCH.copy())
                        # clear BATCH
                        self.BATCH = self.pars.alloc_batch_array()
                    else:
                        # send NACK
                        self.sender.send_nack(self.BATCH)

                # Last batch
                if self.CURR_BATCH_INDEX == self.LAST_BATCH_INDEX and self.CURR_DGRAM_INDEX == self.LAST_DGRAM_INDEX:
                    # if no datagram is missing
                    if not self.pars.find_indices(self.BATCH, lambda x: x is None):
                        if self.IS_FILE:
                            self.sender.send_ack_file(self.CURR_BATCH_INDEX)
                            # TODO save file
                            pass

                        else:
                            # send ACK
                            self.sender.send_ack_msg(self.CURR_BATCH_INDEX)
                            # append FULL_DATA with last/current BATCH
                            self.FULL_DATA.append(self.BATCH.copy())
                            # merge message
                            msg = self.pars.process_message(self.FULL_DATA)
                            # CHAT PRINT
                            print(f'[{self.SRC_ADDR[1]}]({len(msg)}B) {c.YELLOW + msg + c.END}')
                    else:
                        # send NACK
                        self.sender.send_nack(self.BATCH)

        else:
            self.BATCH.insert(self.CURR_DGRAM_INDEX, None)
