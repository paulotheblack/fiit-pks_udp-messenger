import threading, struct, sys, pathlib, math

"""
custom header:
_FLAGS      -- B
_BATCH_NO   -- H
_DGRAM_NO   -- B 
_CRC        -- H
"""


class Sender:
    socket_interface = None
    socket = None  # Sock.sock

    dest_addr = None  # Tuple[str, int]

    _HEADER_SIZE = 7
    _DGRAM_SIZE = 13 - _HEADER_SIZE  # MAX SIZE 1493

    _BATCH_SIZE = 10

    def __init__(self, sock):
        self.socket_interface = sock
        self.socket = sock.get_socket()
        threading.Thread.__init__(self)

    def run(self):
        self.welcome()

        while True:
            action = input('$ >> ')
            if action == ':c':  # establish connection
                self.send_syn()
            if action == ':m':  # send message
                self.send_message()
            if action == ':f':  # send file
                pass
            if action == ':d':  # drop connection [do not send keep-alive]
                pass
            if action == ':s':  # settings for changing port and dgram size
                pass
            if action == ':q':  # quit program
                self.socket_interface.close_socket()
                print('> Goodbye!')
                exit(0)
            else:
                print('> Unknown action, please try again')

    def welcome(self):
        print(
            f'> Welcome!\n'
            f'> Your address is set to: {self.socket.getsockname()}\n'
            f'> type ":c" to establish connection\n'
            f'> then you can ":m" send message or ":f" send file\n'
        )

    def send(self, dgram):
        print(dgram)
        # self.socket.sendto(dgram, self.dest_addr)


    @staticmethod
    def create_dgram(flags, batch_no, dgram_no, data):
        _FLAGS = flags
        _BATCH_NO = batch_no
        _DGRAM_NO = dgram_no
        _CRC = 0000  # TODO implement checksum

        # _DATA = data.encode()
        # _HEADER = struct.pack('!B H H H', _FLAGS, _BATCH_NO, _DGRAM_NO, _CRC)
        _DATA = str(data)
        _HEADER = 'f:' + str(_FLAGS) + ' ' + str(_BATCH_NO) + '-' + str(_DGRAM_NO) + '--- '
        return _HEADER + _DATA

    """
        method be given full message/file
        return List[_BATCH][_SEQ]
    """
    def create_batch(self, flags, full_data):
        _DATA_LEN = len(full_data)

        # DATA can be send in single datagram
        if _DATA_LEN <= self._DGRAM_SIZE:
            info_syn = self.create_dgram(1, 0, 0, self._DGRAM_SIZE)
            return info_syn, self.create_dgram(flags, 0, 0, full_data)

        # DATA can be send in single batch
        elif _DATA_LEN <= self._DGRAM_SIZE * self._BATCH_SIZE:
            batch = []
            DGRAM_COUNT = math.ceil(len(full_data) / self._DGRAM_SIZE)

            for DGRAM_NO in range(0, DGRAM_COUNT):
                data = full_data[(DGRAM_NO * self._DGRAM_SIZE): (DGRAM_NO * self._DGRAM_SIZE + self._DGRAM_SIZE)]
                dgram = self.create_dgram(flags, 0, DGRAM_NO, data)
                batch.append(dgram)

            info_syn = self.create_dgram(1, 0, DGRAM_COUNT, self._DGRAM_SIZE)
            return info_syn, batch

        else:
            batch = []
            message = []

            # get number of batches to send
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

            info_syn = self.create_dgram(1, BATCH_COUNT - 1, DGRAM_NO, self._DGRAM_SIZE)
            return info_syn, message

    """
        send SYN, 
        trying to establish connection
    """
    def send_syn(self):
        dest_addr = '127.0.0.2'  # input('> connect to (IP): ')
        dest_port = 42040  # input('> at port: ')
        self.dest_addr = (dest_addr, int(dest_port))

        _FLAG = 1  # SYN
        # _DATA = self.socket_interface.local_address[0] + ':' + str(self.socket_interface.local_address[1])
        _DATA = 'Hello World'
        _DGRAM = self.create_dgram(_FLAG, 0, 0, _DATA)
        self.send(_DGRAM)
        print(f'... SYN send to {self.dest_addr}')

    """
        send ACK,
        after receiving SYN
        acknowledge connection
    """
    def send_ack(self):
        _FLAG = 2  # ACK
        _DATA = self.socket.local_address[0] + ':' + self.socket.local_address[1]
        _DGRAM = self.create_dgram(_FLAG, 0, 0, _DATA)
        self.send(_DGRAM)
        print(f'> ACK send to {self.dest_addr}')

    def send_message(self):
        data = input('# ')
        info_syn, batch_list = self.create_batch(3, data)

        # SEND SYN WITH INFO ABOUT MESSAGE
        self.send(info_syn)

        # check if 2D List
        if isinstance(batch_list[0], list):
            for batch in batch_list:
                for dgram in batch:
                    self.send(dgram)
                # TODO waiting for ACK before another batch
        else:
            for dgram in batch_list:
                self.send(dgram)
