import time
from select import select

from src.sock import Sock
from src.utils.parser import Parser
from threading import Thread
import src.utils.color as c


class Sender(Thread):
    DEST_ADDR: tuple = None
    CONNECTED: bool = False

    # ARQ + ERR handling flags
    GOT_ACK: bool = False
    ACK_NO: int = None
    GOT_NACK: bool = False

    # Indexes to resend
    TO_RESEND: list = None

    def __init__(self, sock: Sock, parser: Parser):
        Thread.__init__(self, name='Sender', daemon=True)
        self.sockint = sock
        self.socket = sock.get_socket()
        self.parser = parser

    def send(self, dgram, err=False):
        if err:
            dgram = dgram[: -1]

        self.socket.sendto(dgram, self.DEST_ADDR)

    # -------------------  CONNECTION ------------------------- #
    def send_syn(self):
        if self.CONNECTED:
            print(f'{c.RED}[log]{c.END} Already connected to {c.DARKCYAN}{self.DEST_ADDR[0]}:{self.DEST_ADDR[1]}{c.END}')
            return

        while self.DEST_ADDR is None:
            try:
                dest_addr = input('> Connect to (IP): ')
                dest_port = input('> At port: ')
                self.DEST_ADDR = (dest_addr, int(dest_port))
                dgram = self.parser.create_dgram(0, 0, 0, b'')
                self.send(dgram)
            except OSError:
                print(f'> OSError, please try again!')
                self.DEST_ADDR = None

        response = select([self.socket], [], [], 2)
        if not response[0] and not self.CONNECTED:
            print(f'{c.PURPLE + c.BOLD}[log] Destination Unreachable{c.END}')
            self.DEST_ADDR = None
            return

        self.CONNECTED = True

    def send_ack(self):
        dgram = self.parser.create_dgram(1, 0, 0, b'')
        self.send(dgram)

    def send_fin(self, msg='Connection dropped!'):
        if self.CONNECTED:
            dgram = self.parser.create_dgram(10, 0, 0, b'')
            self.send(dgram)

            print(f'{c.RED}[log] {c.PURPLE + c.BOLD}{msg}{c.END}')
            self.DEST_ADDR = None
            self.CONNECTED = False

        else:
            print(f'{c.RED}[log]{c.END} No connection to close')

    # -------------------  ACKs/NACK ------------------------- #
    def send_ack_data(self, batch_no):
        dgram = self.parser.create_dgram(5, batch_no, 0, b'')
        # print(f'[log] sending ACK {batch_no}')
        self.send(dgram)

    def send_nack(self, to_resend):
        nack_field = self.parser.get_nack_field(to_resend)
        dgram = self.parser.create_dgram(6, 0, nack_field, b'')
        # print(f'{c.RED}[log]{c.END} sending NACK')
        self.send(dgram)

    def send_keepalive(self):
        dgram = self.parser.create_dgram(8, 0, 0, b'')
        # print(f'{c.RED}[log]{c.END} sent TTL')
        self.send(dgram)

    # ---------------------  DATA ---------------------------- #
    def input_data(self, file=False, err=False):
        # Check connection first
        if not self.CONNECTED or self.DEST_ADDR is None:
            print(f'{c.RED}[log]{c.END} Not connected to any client!\n'
                  f'> Need to establish connection first (type ":c")')
            return

        if file:
            data = False
            while not data:
                flag = 4
                # absolute path to file
                path = input('> Provide absolute path to file\n# ')
                # if user wants to escape 'file sending'
                if path == ':q':
                    return

                data, file_name = self.parser.get_file(path)

                # Unable to load file, try again
                if not data:
                    return

                # send file_name
                self.send_data(flag=9, data=file_name, err=err)
                # send_file
                self.send_data(flag, data, err)

        else:
            flag = 3
            # user input
            data = input('# ')
            # send_message
            self.send_data(flag, data, err)

    def send_data(self, flag, data, err=False, ratio=7):

        request, batch_list = self.parser.create_batch(flag, data)
        self.send(request)

        # -  SINGLE DATAGRAM --------------------------------------------------- #
        if isinstance(batch_list, bytes):

            if err:
                self.send(batch_list, err=True)
            else:
                self.send(batch_list)

            while self.GOT_ACK is False:
                if self.GOT_NACK:
                    break
                pass

            if self.GOT_NACK:
                self.retransmit_current_batch(batch_list)

            if (flag == 4 or flag == 3) and self.ACK_NO == 0:
                print(f'{c.RED}[log]{c.GREEN} Received!{c.END}')

        # - SINGLE BATCH ------------------------------------------------------- #
        elif isinstance(batch_list[0], bytes):
            if err:
                for batch_index, dgram in enumerate(batch_list):
                    if batch_index % ratio == 0:
                        self.send(dgram, err=True)
                    else:
                        self.send(dgram)
            else:
                for batch_index, dgram in enumerate(batch_list):
                    self.send(dgram)

            while self.GOT_ACK is False:
                if self.GOT_NACK:
                    break
                pass

            if self.GOT_NACK:
                self.retransmit_current_batch(batch_list)

            if (flag == 4 or flag == 3) and self.ACK_NO == 0:
                print(f'{c.RED}[log]{c.GREEN} Received!{c.END}')

        # - MULTIPLE BATCHES --------------------------------------------------- #
        elif isinstance(batch_list[0], list):
            for batch_index, batch in enumerate(batch_list):
                # ARQ Simulation
                if err:
                    for dgram_index, dgram in enumerate(batch):
                        if dgram_index % ratio == 0:
                            self.send(dgram, err=True)
                        else:
                            self.send(dgram)

                # Simple data-transmission
                else:
                    for dgram_index, dgram in enumerate(batch):
                        self.send(dgram)

                while self.GOT_ACK is False:
                    if self.GOT_NACK:
                        break
                    pass

                if self.GOT_NACK:
                    self.retransmit_current_batch(batch)

                # Reset flag
                self.reset_ack_flags()

            if (flag == 4 or flag == 3) and self.ACK_NO == batch_index:
                print(f'{c.RED}[log]{c.GREEN} Received!{c.END}')

        self.reset_ack_flags()

    # ---------------------  MISC ---------------------------- #
    def reset_ack_flags(self):
        self.GOT_ACK = False
        self.GOT_NACK = False

    def retransmit_current_batch(self, batch):
        self.GOT_NACK = False
        # Because of print -_- (too fast)
        time.sleep(0.00001)

        print(f'{c.RED}[log]{c.END} Retransmission of dgrams {self.TO_RESEND}')

        if isinstance(batch, bytes):
            self.send(batch)

        else:
            for i, dgram in enumerate(batch):
                if i in self.TO_RESEND:
                    self.send(dgram)

        while self.GOT_ACK is False:
            pass

        if self.GOT_NACK:
            self.retransmit_current_batch(batch)



