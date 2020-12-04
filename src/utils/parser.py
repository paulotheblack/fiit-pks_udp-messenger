import math
import struct
import argparse
import textwrap
import itertools
import pathlib as p
import src.utils.color as c

"""
custom header: 8B
_FLAGS      -- B (1B)
_BATCH_NO   -- I (4B)
_DGRAM_NO   -- B (1B)
_CRC        -- H (2B)

_FLAGS:
    0: SYN (two-way handshake)
    1: ACK (     ___||___     )
    2: REQUEST [LAST_BATCH, LAST_DGRAM, CRC, data='3(MSG) or 4(FILE)']
    3: MSG 
    4: FILE
    5: ACK_DATA
    7: NACK
    8: KEEP_ALIVE
    9: FILE_NAME
    10: FIN
"""


class Parser:
    HEADER_SIZE = 8
    DGRAM_SIZE = 1448  # MAX SIZE 1450
    BATCH_SIZE = 8  # MAX 8

    VARS = None

    # ------------------ UTILS --------------------- #
    # DONE
    def parse_args(self):
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
        ap.add_argument('-f', help='Path to save files')
        args = ap.parse_args()
        self.VARS = vars(args)
        return vars(args)

    # DONE
    def get_args(self):
        return self.VARS

    # DONE
    def set_dgram_size(self):
        """
            User defined DATAGRAM size (in B)

            Value can be only between 1 and 1440
        """
        print(
            f'HEADER_SIZE: {self.HEADER_SIZE}\n'
            f'DGRAM_SIZE: {self.DGRAM_SIZE}\n'
            f'BATCH_SIZE: {self.BATCH_SIZE}'
        )

        desired_size = int(input('> SET DGRAM_SIZE to (in B): '))

        while desired_size < 1 or desired_size > 1450:
            desired_size = int(input('! Incorrect DGRAM_SIZE\n> in B (min. 1, max.1440): '))

        self.DGRAM_SIZE = desired_size
        print(f'{c.RED}[log] NEW DGRAM_SIZE = {self.DGRAM_SIZE}B{c.END}')

    # DONE
    @staticmethod
    def crc16(data: bytes, poly=0x8408):
        """
            CRC-16-CCITT Algorithm

            source: https://gist.github.com/oysstu/68072c44c02879a2abf94ef350d1c7c6
        """
        data = bytearray(data)
        crc = 0xFFFF
        for b in data:
            cur_byte = 0xFF & b
            for _ in range(0, 8):
                if (crc & 0x0001) ^ (cur_byte & 0x0001):
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
                cur_byte >>= 1
        crc = (~crc & 0xFFFF)
        crc = (crc << 8) | ((crc >> 8) & 0xFF)

        return crc & 0xFFFF

    # DONE
    def check_sum(self, header, data):
        crc_header = struct.pack('!B I B H', header[0], header[1], header[2], 0)
        crc_data = crc_header + data

        crc = self.crc16(crc_data)
        if crc == header[3]:
            return True
        else:
            return False

    # DONE
    @staticmethod
    def get_file(path: str):
        try:
            posix_path = p.Path(path)
            with posix_path.open(mode='r') as f:
                data = posix_path.read_bytes()
                return data, posix_path.name
        except IOError:
            print(f'{c.RED}> Unable to read file{c.END}')
            return None, None

    # DONE
    def write_file(self, path: str, name: str, data):
        """
            TODO add doc string

            args

            return:
                size_readable   / None
                posix_path      / None
        """
        try:
            with open("".join([path, name]), 'wb') as f:
                # size = len(data)
                # size_readable = self.convert_size(len(data))

                if isinstance(data[0], list):
                    for batch in data:
                        for dgram in batch:
                            f.write(dgram)

                elif isinstance(data, list):
                    for dgram in data:
                        f.write(dgram)
                else:
                    f.write(data)

                f.close()

                posix_path = p.Path("".join([path, name]))
                size = posix_path.stat().st_size
                size_readable = self.convert_size(size)
                return posix_path, size_readable

        except IOError:
            print(IOError.strerror + '' + IOError.errno)
            return None, None

    # DONE
    @staticmethod
    def convert_size(num):
        """
            source: https://stackoverflow.com/a/39988702
        """
        for x in ['B', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0

    # ------------ DGRAM DECOMPOSITION -------------- #
    # DONE
    def get_header(self, dgram):
        return struct.unpack('!B I B H', dgram[:self.HEADER_SIZE])

    # DONE
    def get_data(self, dgram):
        return dgram[self.HEADER_SIZE:]

    # ------------- DGRAM COMPOSITION --------------- #
    # DONE
    def create_dgram(self, flag, batch_no, dgram_no, data: bytearray):
        """
            TODO add docstring

            args:
                flag: int
                batch_no: int
                dgram_no: int
                data: bytearray

            return:
                DGRAM: bytearray

            note:
        """
        # HEADER_ just for getting checksum (CRC assigned as 0)
        _HEADER = struct.pack('!B I B H', flag, batch_no, dgram_no, 0)
        _DGRAM = _HEADER + data

        # compute checksum
        CRC = self.crc16(_DGRAM)

        # HEADER with proper checksum
        HEADER = struct.pack('!B I B H', flag, batch_no, dgram_no, CRC)
        return HEADER + data

    # DONE
    def create_batch(self, flag, full_data):
        """
            Parse input data to batches of datagrams

            args:
                flags: int      flag for header (type of DATA)
                full_data:      data to parse

            return:
                request: bytearray  request datagram with type of data as payload
                -----
                dgram: bytearray -               if message can be send in single DGRAM
                batch: [bytearray] -             if message can be send in single batch
                list_of_batches: [[bytearray]] - if message need to be send in list of batches

        """
        # if message, need to encode
        if flag == 3 or flag == 9:
            _DATA = full_data.encode()
        else:
            _DATA = full_data

        _DATA_LEN = len(_DATA)
        _FLAG_B = str(flag).encode()

        # SINGLE DATAGRAM
        if _DATA_LEN <= self.DGRAM_SIZE:
            request = self.create_dgram(2, 0, 0, _FLAG_B)  # REQUEST
            return request, self.create_dgram(flag, 0, 0, _DATA)

        # ------------------------------------------------ #
        # SINGLE BATCH of DGRAMs
        elif _DATA_LEN <= self.DGRAM_SIZE * self.BATCH_SIZE:
            batch = []
            DGRAM_COUNT = math.ceil(len(_DATA) / self.DGRAM_SIZE)

            for dgram_index in range(0, DGRAM_COUNT):
                payload = _DATA[(dgram_index * self.DGRAM_SIZE): (dgram_index * self.DGRAM_SIZE + self.DGRAM_SIZE)]
                dgram = self.create_dgram(flag, 0, dgram_index, payload)
                batch.append(dgram)

            request = self.create_dgram(2, 0, DGRAM_COUNT - 1, _FLAG_B)  # REQUEST
            return request, batch

        # ------------------------------------------------ #
        # DATA needs to be send in multiple batches
        else:
            if flag == 4:
                print(f'{c.RED + "[log]" + c.END} Parsing file... ', end='')

            batch = []
            list_of_batches = []

            BATCH_COUNT = math.ceil((len(_DATA) / self.DGRAM_SIZE) / self.BATCH_SIZE)

            start = 0
            end = self.DGRAM_SIZE

            for BATCH_NO in range(0, BATCH_COUNT):
                batch.clear()

                for dgram_index in range(0, self.BATCH_SIZE):
                    payload = _DATA[start: end]
                    dgram = self.create_dgram(flag, BATCH_NO, dgram_index, payload)
                    batch.append(dgram)

                    start += self.DGRAM_SIZE
                    end = start + self.DGRAM_SIZE

                    if start >= _DATA_LEN:
                        break

                list_of_batches.append(batch.copy())

            request = self.create_dgram(2, BATCH_COUNT - 1, dgram_index, _FLAG_B)  # REQUEST

            if flag == 4:
                print(f'{c.RED}DONE!{c.END}')

            return request, list_of_batches

    # --------------- MSG HANDLING ----------------- #
    # DONE
    def create_data_buffer(self, last_batch_index, last_dgram_index):
        # - SINGLE DGRAM - #
        if last_batch_index == 0 and last_dgram_index == 0:
            return [[b'']]
        # - SINGLE BATCH - #
        elif last_batch_index == 0:
            return [[b'' for x in range(last_dgram_index + 1)] for y in range(last_batch_index + 1)]
        # - MULTI BATCH - #
        else:
            buff = [[b'' for x in range(self.BATCH_SIZE)] for y in range(last_batch_index)]
            buff.append([b'' for x in range(last_dgram_index + 1)])
        return buff

    # DONE
    @staticmethod
    def process_message(recv_data_buffer):
        """
            Merge and decode received message

            args:

            return:
                :str
        """
        if isinstance(recv_data_buffer[0], list):
            for batch in recv_data_buffer:
                for i, dgram in enumerate(batch):
                    if isinstance(dgram, bytes):
                        batch[i] = dgram.decode()

        elif isinstance(recv_data_buffer, list):
            for i, dgram in enumerate(recv_data_buffer):
                if isinstance(dgram, bytes):
                    recv_data_buffer[i] = dgram.decode()
        else:
            recv_data_buffer.decode()

        return ''.join(itertools.chain(*recv_data_buffer))

    # --------------- NACK HANDLING ---------------- #
    # DONE
    @staticmethod
    def set_bit(n, k):
        """
            Set k-th bit as 1

            Usage:
                NACK is using (header)-DGRAM_NO field as indication for missing datagrams.

            return:
                updated n
        """
        return (1 << k) | n

    # DONE
    @staticmethod
    def find_index(arr: list, condition):
        return [i for i, elem in enumerate(arr) if condition(elem)]

    # DONE
    def get_nack_field(self, to_resend: list):
        """
            create 1B field with indications of missing datagrams

            bit set to 1 represents index of DGRAM in BATCH to resend

            args:
                indexes:list - list of

            return:
                0bxxxxxxxx
        """

        nack_field = 0b00000000
        # to_resend = self.find_index(batch, lambda x: x is None)

        for index in to_resend:
            nack_field = self.set_bit(nack_field, index)

        return nack_field

    # DONE
    def parse_nack_field(self, header):
        """

            TODO add docstring

            ta ti ja viem
        """
        nack_field = header[2]

        return self.find_index(reversed(list(f'{nack_field:08b}')), lambda x: x == '1')
