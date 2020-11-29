import math
import struct
import argparse
import textwrap

"""
custom header: 8B
_FLAGS      -- B (1B)
_BATCH_NO   -- I (4B)
_DGRAM_NO   -- B (1B)
_CRC        -- H (2B)

_FLAGS:
    0: SYN (two-way handshake)
    1: ACK (      --||--     )
    2: REQUEST [LAST_BATCH, LAST_DGRAM, CRC, data='3(MSG) or 4(FILE)']
    3: MSG 
    4: FILE
    5: ACK_MSG
    6: ACK_FILE
    7: NACK
    8: KEEP_ALIVE
"""


class Parser:
    HEADER_SIZE = 8
    DGRAM_SIZE = 158 - HEADER_SIZE  # MAX SIZE 1492
    BATCH_SIZE = 8  # MAX 8

    @staticmethod
    def parse_args():
        ap = argparse.ArgumentParser(
            prog='UDP_Messenger',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
                    # ----------------------------------------------- #
                    #   UDP Messenger, PKS assigment 2. v0.1          #
                    #       Author:     Michal Paulovic               #
                    #       STU-FIIT:   xpaulovicm1                   #
                    #       Github:     paulotheblack                 #
                    #   https://github.com/paulotheblack/udp_msngr    #
                    # ----------------------------------------------- #
                '''))

        ap.add_argument('-a', help='Local IP address to bind')
        ap.add_argument('-p', help='Local Port to bind')
        args = ap.parse_args()
        return vars(args)

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

    def get_header(self, dgram):
        return struct.unpack('!B I B H', dgram[:self.HEADER_SIZE])

    def get_data(self, dgram):
        return dgram[self.HEADER_SIZE:]

    # ------------------------------------------------ #

    @staticmethod
    def create_dgram(flags, batch_no, dgram_no, data):
        CRC = 65535  # TODO implement checksum
        DATA = str(data).encode()
        HEADER = struct.pack('!B I B H', flags, batch_no, dgram_no, CRC)
        return HEADER + DATA

    # parse data to dgrams/batches of dgrams
    def create_batch(self, flags, full_data):
        _DATA_LEN = len(full_data)

        # DATA can be send in single datagram
        if _DATA_LEN <= self.DGRAM_SIZE:
            info_syn = self.create_dgram(2, 0, 0, flags)  # REQUEST
            return info_syn, self.create_dgram(flags, 0, 0, full_data)

        # ------------------------------------------------ #
        # DATA can be send in single batch
        elif _DATA_LEN <= self.DGRAM_SIZE * self.BATCH_SIZE:
            batch = []
            DGRAM_COUNT = math.ceil(len(full_data) / self.DGRAM_SIZE)

            for DGRAM_NO in range(0, DGRAM_COUNT):
                data = full_data[(DGRAM_NO * self.DGRAM_SIZE): (DGRAM_NO * self.DGRAM_SIZE + self.DGRAM_SIZE)]
                dgram = self.create_dgram(flags, 0, DGRAM_NO, data)
                batch.append(dgram)

            info_syn = self.create_dgram(2, 0, DGRAM_COUNT - 1, flags)  # REQUEST
            return info_syn, batch

        # ------------------------------------------------ #
        # DATA needs to be send in multiple batches
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

            info_syn = self.create_dgram(2, BATCH_COUNT - 1, DGRAM_NO, flags)  # REQUEST
            return info_syn, message

    # ------------------------------------------------ #
