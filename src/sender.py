import threading, struct, sys, pathlib, math

"""
custom header:
_FLAGS -- B
_BATCH -- H
_SEQ   -- B 
_CRC   -- H
_LEN   -- H
"""


class Sender:
    socket_interface = None
    socket = None  # Sock.sock

    dest_addr = None  # Tuple[str, int]

    _HEADER_SIZE = 10
    _DGRAM_SIZE = 1500 - _HEADER_SIZE  # MAX SIZE 1490

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
                pass
            if action == ':f':  # send file
                pass
            if action == ':d':  # drop connection [do not send keep-alive]
                pass
            if action == ':s':  # settings for changing port and dgram size
                pass
            if action == ':q':  # quit program
                self.socket_interface.close_socket()
                print('Goodbye! ..')
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

    def send(self, dgram, addr=dest_addr):
        self.socket.sendto(dgram, addr)

    @staticmethod
    def create_dgram(flags, batch_no, seq_no, data):
        _FLAGS = flags
        _BATCH = batch_no
        _SEQ = seq_no
        _CRC = 123456  # TODO implement checksum
        _LEN = len(data)

        header = struct.pack('!B H B H H', _FLAGS, _BATCH, _SEQ, _CRC, _LEN)
        return header + data

    """
        method be given full message/file
        return List[_BATCH][_SEQ]
    """
    def create_batch(self, flags, full_data):
        _DATA_LEN = len(full_data)

        # DATA can be send in single datagram
        if _DATA_LEN <= self._DGRAM_SIZE:
            return [full_data.encode()]

        # DATA can be send in single batch
        elif _DATA_LEN <= self._DGRAM_SIZE * 10:
            batch = []
            seq_count = math.ceil(len(full_data) / self._DGRAM_SIZE)

            for i in range(0, seq_count):
                batch.append(full_data[(i * self._DGRAM_SIZE): (i * self._DGRAM_SIZE + self._DGRAM_SIZE)].encode())
            return batch

    """
        send SYN, 
        trying to establish connection
    """
    def send_syn(self):
        dest_addr = input('> connect to (IP): ')
        dest_port = input('> at port: ')
        self.dest_addr = (dest_addr, int(dest_port))

        _FLAG = 1  # SYN
        _DATA = self.socket.local_address.encode()
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
        _DATA = self.socket.local_address.encode()
        _DGRAM = self.create_dgram(_FLAG, 0, 0, _DATA)
        self.send(_DGRAM)
