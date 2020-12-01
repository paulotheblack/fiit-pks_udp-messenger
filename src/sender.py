from src.sock import Sock
from src.utils.parser import Parser
from threading import Thread
import src.utils.color as c


class Sender(Thread):
    DEST_ADDR: tuple = None

    # ARQ + ERR handling flags
    GOT_ACK: bool = None
    ACK_NO: int = None
    GOT_NACK: bool = None
    # Indexes to resend
    TO_RESEND: list = None

    def __init__(self, sock: Sock, parser: Parser):
        Thread.__init__(self, name='Sender', daemon=True)
        self.sockint = sock
        self.socket = sock.get_socket()
        self.parser = parser

    def send(self, dgram):
        self.socket.sendto(dgram, self.DEST_ADDR)

    # -------------------  HANDSHAKE ------------------------- #
    def send_syn(self):
        dest_addr = input('> Connect to (IP): ')
        dest_port = input('> At port: ')
        self.DEST_ADDR = (dest_addr, int(dest_port))
        dgram = self.parser.create_dgram(0, 0, 0, b'')
        self.send(dgram)

        while self.GOT_ACK is False:
            # TODO implement KEEP_ALIVE
            pass

        # Reset flag
        self.GOT_ACK = False

    def send_ack(self):
        dgram = self.parser.create_dgram(1, 0, 0, b'')
        self.send(dgram)

    # -------------------  ACKs/NACK ------------------------- #
    def send_ack_msg(self, batch_no):
        dgram = self.parser.create_dgram(5, batch_no, 0, b'')
        self.send(dgram)

    def send_ack_file(self, batch_no):
        dgram = self.parser.create_dgram(6, batch_no, 0, b'')
        self.send(dgram)

    def send_nack(self, batch):
        nack_field = self.parser.get_nack_field(batch)
        dgram = self.parser.create_dgram(7, 0, nack_field, b'')
        self.send(dgram)

    # ---------------------  DATA ---------------------------- #
    def input_data(self, file=False):
        if file:
            data = False
            while not data:
                flag = 4
                path = input('> Provide absolute path to file\n# ')
                if path == ':q':
                    return

                data, file_name = self.parser.get_file(path)

                if not data:
                    return

                # send file_name
                self.send_data(flag=9, data=file_name)
                # send_file
                self.send_data(flag, data)

        else:
            flag = 3
            data = input('# ')
            # send_message
            self.send_data(flag, data)

    def send_data(self, flag, data):
        """
            Send data from user

            args:
                file: if data type is File (default=False)

            Runtime:
                1. parse data
                2. send REQUEST
                3. send message
                if single datagram:
                    not waiting for ACK
                if single batch:
                    waiting for ACK in case of retransmission
                if bunch of batches:
                    waiting for ACK after each batch in case of retransmission

            return: void
        """

        request, batch_list = self.parser.create_batch(flag, data)
        self.send(request)

        # TODO ask if want to receive file!

        # -  SINGLE DATAGRAM --------------------------------------------------- #
        if isinstance(batch_list, bytes):
            self.send(batch_list)

            # do not send next batch until MSG_ACK or NACK received
            while self.GOT_ACK is False or self.GOT_NACK is False:
                pass
            if self.GOT_NACK:
                print('GOT NACK')
                self.retransmission(batch_list)

            # Reset flag
            self.GOT_ACK = False

        # - SINGLE BATCH ------------------------------------------------------- #
        elif isinstance(batch_list[0], bytes):
            for dgram in batch_list:
                self.send(dgram)

            # do not send next batch until MSG_ACK or NACK received
            while self.GOT_ACK is False or self.GOT_NACK is False:
                pass
            if self.GOT_NACK:
                print('GOT NACK')
                self.retransmission(batch_list)

            # Reset flag
            self.GOT_ACK = False

        # - MULTIPLE BATCHES --------------------------------------------------- #
        elif isinstance(batch_list[0], list):
            for i, batch in enumerate(batch_list):
                self.GOT_ACK = False

                for dgram in batch:
                    self.send(dgram)

                # do not send next batch until MSG_ACK or NACK received
                while self.GOT_ACK is False or self.GOT_NACK is False:
                    pass
                if self.GOT_NACK:
                    print('GOT NACK')
                    self.retransmission(batch)

                # Reset flag
                self.GOT_ACK = False

            if flag == 4 and self.ACK_NO == i:
                print(f'{c.RED}[log]{c.GREEN} File received!')

        # STDERR
        else:
            print(f'[TYPE ERR]: {type(batch_list)}\n {batch_list}')

    def retransmission(self, batch: list):
        for i, dgram in enumerate(batch):
            if i in self.TO_RESEND:
                self.send(dgram)

        while self.GOT_ACK is False or self.GOT_NACK is False:
            pass
        if self.GOT_NACK:  # OR KEEP_ALIVE
            self.retransmission(batch)
