import logging
import socket
from pytimer import TmuxHelper

class DaemonState:
    AWAIT_MSG = None

    def __init__(self):
        self.socket = socket.socket()
        self.done = False
        self.value = None
        self.fault = False

    def state_init(self):
        logging.info(f"Initializing state: {self}")

    def __str__(self):
        return self.__class__.__name__

    def next(self):
        raise NotImplementedError

    def handle_msgs(self):
        raise NotImplementedError

    def get_msgs(self):
        while True:
            response = self.socket.recv(1024)
            response = response.decode()
            response = response.split(";")

            # continue if no data sent
            if len(response) == 1:
                continue

            response = response[:-1]

            if self.queue == None:
                self.queue = response
            else:
                self.queue = self.queue + response

            if self.AWAIT_MSG in response:
                break


class SynAck(DaemonState):
    AWAIT_MSG = "SYN ACK"

    def __init__(self, socket: socket.socket, queue=[]):
        self.socket = socket
        self.done = False
        self.value = None
        self.queue = queue
        self.fault = False


    def handle_msgs(self):
        if len(self.queue) == 0:
            self.get_msgs()

        response = self.queue
        self.queue = []

        if self.AWAIT_MSG not in response:
            TmuxHelper.message_create(f"{self} expected {self.AWAIT_MSG}")
            self.fault = True
            self.next()

        response = response[response.index(self.AWAIT_MSG):]

        while True:
            msg = response.pop(0)
            if msg != self.AWAIT_MSG:
                TmuxHelper.message_create(f"{self} expected {self.AWAIT_MSG}, but recieved {msg}")
                self.fault = True

                break
            else:
                if len(response) > 0:
                    self.queue = response

                break


    def next(self):
        self.handle_msgs()

        if self.fault:
            return Done(self.socket)

        return Ack(self.socket, queue=self.queue)


class Ack(DaemonState):
    AWAIT_MSG = "ACK"

    def __init__(self, socket: socket.socket, queue=[]):
        self.socket = socket
        self.done = False
        self.value = []
        self.queue = queue
        self.fault = False

    def handle_msgs(self):
        if len(self.queue) == 0:
            self.get_msgs()
        elif self.queue[0] != self.AWAIT_MSG:
            self.get_msgs()

        response = self.queue
        self.queue = []

        if self.AWAIT_MSG not in response:
            TmuxHelper.message_create(f"{self} expected {self.AWAIT_MSG}")
            self.fault = True
            self.next()

        while True:
            msg = response.pop(0)
            if msg != self.AWAIT_MSG:
                self.value.append(msg)
            else:
                if len(response) > 0:
                    self.queue = response

                break


    def next(self):
        self.handle_msgs()
        for val in self.value:
            print(val)

        if len(self.queue) == 0:
            return Done(self.socket, value=self.value)

        if len(self.queue) > 0:
            if self.queue[0] == SynAck.AWAIT_MSG:
                return SynAck(self.socket, queue=self.queue)
            elif Ack.AWAIT_MSG in self.queue:
                return Ack(self.socket, queue=self.queue)
            else:
                TmuxHelper.message_create("Unexpected data received after ACK")
        else:
            TmuxHelper.message_create("Msgs provided to ACK, but no messages present")

        return Done(self.socket, value=self.value)


class Done(DaemonState):
    def __init__(self, socket: socket.socket, value=[]):
        self.socket = socket
        self.value = value
        self.queue = []
        self.fault = False

        self.socket.close()
