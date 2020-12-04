from threading import Thread, Event
import time


class KeepAlive(Thread):

    RECV_TTL: bool = None
    TIMER: int = None
    START = None
    STOP = False
    KILL = False

    def __init__(self, sender):
        self.sender = sender
        Thread.__init__(self, name='KeepAlive', daemon=True)

    def run(self):
        time.sleep(10)

        # Thread should run all the time
        while True:
            time.sleep(10)
            # if flag set to start
            if self.START:
                self.session()
            if self.KILL:
                return

    def session(self):
        self.STOP = False
        self.TIMER = 10
        time.sleep(5)

        while self.sender.CONNECTED:
            self.sender.send_keepalive()
            time.sleep(5)

            self.TIMER -= 5
            if self.RECV_TTL:
                self.TIMER += 5
                self.RECV_TTL = False

            if self.TIMER <= 0:
                if self.sender.CONNECTED:
                    self.sender.send_fin(msg=f'[{self.sender.DEST_ADDR[0]}] Timed Out!')
                    self.START = False
                    return

            if self.STOP:
                self.START = False
                return
