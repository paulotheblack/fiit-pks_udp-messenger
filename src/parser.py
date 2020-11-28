import math
import struct
import threading

"""
custom header:
_FLAGS      -- B (1B)
_BATCH_NO   -- I (4B)
_DGRAM_NO   -- B (1B)
_CRC        -- H (2B)

_FLAGS:
    1: SYN
    2: SYN_MSG
    3: SYN_FILE
    4: ACK
    5: ACK_MSG
    6: ACK_FILE
    7: TTL
"""


class Parser:
    sockint = None  # custom socket interface 'class Socket'
    socket = None  # Sock.sock
    dest_addr = None  # Tuple[str, int]

    _HEADER_SIZE = 7
    _DGRAM_SIZE = 157 - _HEADER_SIZE  # MAX SIZE 1493
    _BATCH_SIZE = 8  # MAX

    def __init__(self, sock):
        self.sockint = sock
        self.socket = sock.get_socket()
        threading.Thread.__init__(self)

    def get_info(self):
        print(
            f'--------------------------\n'
            f'|>     HEADER_SIZE: {self._HEADER_SIZE}\n'
            f'|>     DGRAM_SIZE: {self._DGRAM_SIZE}\n'
            f'|>     BATCH_SIZE: {self._BATCH_SIZE}\n'
            f'--------------------------\n'
        )

    def set_dgram(self):
        self._DGRAM_SIZE = int(input('$ Desired DGRAM_SIZE in B (min. 1): '))

    def send(self, dgram):
        print(dgram)
        self.socket.sendto(dgram, self.dest_addr)

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
        if _DATA_LEN <= self._DGRAM_SIZE:
            info_syn = self.create_dgram(1, 0, 0, self._BATCH_SIZE)
            return info_syn, self.create_dgram(flags, 0, 0, full_data)

        # DATA can be send in single batch
        elif _DATA_LEN <= self._DGRAM_SIZE * self._BATCH_SIZE:
            batch = []
            DGRAM_COUNT = math.ceil(len(full_data) / self._DGRAM_SIZE)

            for DGRAM_NO in range(0, DGRAM_COUNT):
                data = full_data[(DGRAM_NO * self._DGRAM_SIZE): (DGRAM_NO * self._DGRAM_SIZE + self._DGRAM_SIZE)]
                dgram = self.create_dgram(flags, 0, DGRAM_NO, data)
                batch.append(dgram)

            info_syn = self.create_dgram(1, 0, DGRAM_COUNT, self._BATCH_SIZE)
            return info_syn, batch

        else:
            batch = []
            message = []

            BATCH_COUNT = math.ceil((len(full_data) / self._DGRAM_SIZE) / self._BATCH_SIZE)

            start = 0
            end = self._DGRAM_SIZE

            for BATCH_NO in range(0, BATCH_COUNT):
                batch.clear()

                for DGRAM_NO in range(0, self._BATCH_SIZE):
                    data = full_data[start: end]
                    dgram = self.create_dgram(flags, BATCH_NO, DGRAM_NO, data)
                    batch.append(dgram)

                    start += self._DGRAM_SIZE
                    end = start + self._DGRAM_SIZE

                    if start > _DATA_LEN:
                        break

                message.append(batch.copy())

            info_syn = self.create_dgram(1, BATCH_COUNT - 1, DGRAM_NO, self._BATCH_SIZE)
            return info_syn, message

    def send_syn(self):
        # dest_addr = input('> connect to (IP)')
        # dest_port = input('> at port: ')
        dest_addr = '127.0.0.2'  # input('> connect to (IP): ')
        dest_port = 42040  # input('> at port: ')
        self.dest_addr = (dest_addr, int(dest_port))

        _FLAG = 1  # SYN
        _DGRAM = self.create_dgram(_FLAG, 0, 0, '')
        self.send(_DGRAM)
        print(f'... SYN send to {self.dest_addr}')

    def send_ack(self):
        _FLAG = 2  # ACK
        _DATA = self.socket.local_address[0] + ':' + self.socket.local_address[1]
        _DGRAM = self.create_dgram(_FLAG, 0, 0, _DATA)
        self.send(_DGRAM)
        print(f'> ACK send to {self.dest_addr}')

    def send_message(self):
        data = input('# ').strip('n')
        info_syn, batch_list = self.create_batch(3, data)
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
