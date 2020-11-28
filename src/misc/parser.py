import math
import struct
from threading import Thread

"""
custom header: 8B
_FLAGS      -- B (1B)
_BATCH_NO   -- I (4B)
_DGRAM_NO   -- B (1B)
_CRC        -- H (2B)

_FLAGS:
    0: SYN
    1: ACK
    2: SYN_MSG
    3: SYN_FILE
    4: NACK
    5: KEEP_ALIVE
    6: 
"""


class Parser:
    sockint = None  # custom socket interface 'class Socket'
    socket = None  # Sock.sock
    dest_addr = None  # Tuple[str, int]

    HEADER_SIZE = 7
    DGRAM_SIZE = 157 - HEADER_SIZE  # MAX SIZE 1493
    BATCH_SIZE = 8  # MAX

    def __init__(self, sock):
        self.sockint = sock
        self.socket = sock.get_socket()

    def get_info(self):
        print(
            f'--------------------------\n'
            f'|>     HEADER_SIZE: {self.HEADER_SIZE}\n'
            f'|>     DGRAM_SIZE: {self.DGRAM_SIZE}\n'
            f'|>     BATCH_SIZE: {self.BATCH_SIZE}\n'
            f'--------------------------\n'
        )

    def set_dgram_size(self):
        self.DGRAM_SIZE = int(input('$ Desired DGRAM_SIZE in B (min. 1): '))

    # ------------------------------------------------ #

    @staticmethod
    def create_dgram(flags, batch_no, dgram_no, data):
        CRC = 0000  # TODO implement checksum
        DATA = str(data).encode()
        HEADER = struct.pack('!B I B H', flags, batch_no, dgram_no, CRC)
        # DATA = str(data)
        # HEADER = 'f:' + ' ' + str(batch_no) + '-' + str(dgram_no) + '--- '
        return HEADER + DATA

    # parse data to dgrams/batches of dgrams
    def create_batch(self, flags, full_data):
        _DATA_LEN = len(full_data)

        # DATA can be send in single datagram
        if _DATA_LEN <= self.DGRAM_SIZE:
            info_syn = self.create_dgram(0, 0, 0, self.BATCH_SIZE)
            return info_syn, self.create_dgram(flags, 0, 0, full_data)

        # DATA can be send in single batch
        elif _DATA_LEN <= self.DGRAM_SIZE * self.BATCH_SIZE:
            batch = []
            DGRAM_COUNT = math.ceil(len(full_data) / self.DGRAM_SIZE)

            for DGRAM_NO in range(0, DGRAM_COUNT):
                data = full_data[(DGRAM_NO * self.DGRAM_SIZE): (DGRAM_NO * self.DGRAM_SIZE + self.DGRAM_SIZE)]
                dgram = self.create_dgram(flags, 0, DGRAM_NO, data)
                batch.append(dgram)

            info_syn = self.create_dgram(0, 0, DGRAM_COUNT, self.BATCH_SIZE)
            return info_syn, batch

        else:
            batch = []
            message = []

            BATCH_COUNT = math.ceil((len(full_data) / self.DGRAM_SIZE) / self.BATCH_SIZE)

            start = 0
            end = self.DGRAM_SIZE

            for BATCH_NO in range(0, BATCH_COUNT):
                batch.clear()

                for DGRAM_NO in range(0, self.BATCH_SIZE):
                    data = full_data[start: end]
                    dgram = self.create_dgram(flags, BATCH_NO, DGRAM_NO, data)
                    batch.append(dgram)

                    start += self.DGRAM_SIZE
                    end = start + self.DGRAM_SIZE

                    if start > _DATA_LEN:
                        break

                message.append(batch.copy())

            info_syn = self.create_dgram(0, BATCH_COUNT - 1, DGRAM_NO, self.BATCH_SIZE)
            return info_syn, message

    # ------------------------------------------------ #

    @staticmethod
    def get_header(dgram):
        return struct.unpack('!B I B H', dgram[:8])

    @staticmethod
    def get_data(dgram):
        return dgram[8:]