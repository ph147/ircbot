#!/usr/bin/python


import re
import socket
import logging

from message import Message
from select import select
from contextlib import contextmanager


DEBUG = False

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def log_input(msg):
    logging.debug('<<< {}'.format(msg))


def log_output(msg):
    logging.debug('>>> {}'.format(msg))


@contextmanager
def socket_open(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        yield sock
    finally:
        logging.info('Closing connection...')
        sock.close()


class Connection(object):
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.buf = ''
        self.ident = None
        self.connected = False
        self.socket = None

    def increase_buffer(self):
        data = self.socket.recv(1024)
        if data:
            self.buf += data

    def poll_socket(self):
        incoming, _, _ = select([self.socket], [], [])
        if incoming:
            self.increase_buffer()

    def process_buffer(self):
        while '\r\n' in self.buf:
            lines = re.split(r'(\r\n)', self.buf)
            self.buf = ''.join(lines[2:])
            yield lines[0]

    def recv_data(self):
        while True:
            self.poll_socket()
            for line in self.process_buffer():
                yield line

    def recv_lines(self):
        with socket_open(self.host, self.port) as self.socket:
            for line in self.recv_data():
                log_input(line)
                yield line

    def get_server_ident(self, msg):
        if not self.ident:
            self.ident = msg.sender
            logging.info(
                'Connection established with {}.'.format(msg.sender))

    def recv_messages(self):
        for line in self.recv_lines():
            msg = Message(line)
            self.get_server_ident(msg)
            yield msg

    def send(self, text):
        log_output(text)
        self.socket.send('{}\r\n'.format(text))
