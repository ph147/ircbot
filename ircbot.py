#!/usr/bin/python

import re
import sys
import socket
import logging

from message import Message
from botcommands import ACTIONS, FUNCS
from select import select
from contextlib import contextmanager

DEBUG = False

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


SERVER_WELCOME = '001'
OWNER = 'TheDoctor'


@contextmanager
def socket_open(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        yield sock
    finally:
        logging.info('Closing connection...')
        sock.close()


def log_input(msg):
    logging.debug('<<< {}'.format(msg))


def log_output(msg):
    logging.debug('>>> {}'.format(msg))


def get_command(msg):
    return msg.split()[0][1:]


def is_command(msg):
    return msg.startswith('!')


class IRCBot(object):
    def __init__(self, host=None, port=6667, nick=None, channel=None):
        self.channel = channel or '#helmsdeep'
        self.nick = nick or 'Belthazor'
        self.host = host or 'localhost'
        self.port = port
        self.buf = ''
        self.ident = None
        self.connected = False
        self.socket = None

    def send_credentials(self):
        self.send_nick()
        self.send_user()

    def send_user(self):
        self.send('USER my name * * :name')

    def send_nick(self):
        logging.info('Setting nick to {}.'.format(self.nick))
        self.send('NICK {}'.format(self.nick))

    def join_channel(self):
        logging.info('Joining channel {}...'.format(self.channel))
        self.send('JOIN {}'.format(self.channel))

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
                yield line

    def send(self, text):
        log_output(text)
        self.socket.send('{}\r\n'.format(text))

    def channel_msg(self, text, channel=None):
        channel = channel or self.channel
        self.send('PRIVMSG {} {}'.format(channel, text))

    send_query = channel_msg

    def channel_action(self, text):
        self.channel_msg('\x01ACTION {}\x01'.format(text))

    def process_command(self, command, sender):
        if command in ACTIONS:
            self.channel_action(
                ACTIONS[command].format(nick=sender))
        elif command in FUNCS:
            result = FUNCS[command]().format(nick=sender)
            self.channel_msg(result)

    def process_chan_msg(self, msg):
        if is_command(msg.text):
            command = get_command(msg.text)
            self.process_command(command, msg.sender)

    def process_server_msg(self, msg):
        if not self.connected:
            self.connected = True
            logging.info('Connection established.')
            self.send_credentials()
        elif msg.keyword == SERVER_WELCOME:
            self.join_channel()

    def is_chan_msg(self, msg):
        return msg.keyword == 'PRIVMSG' and msg.channel == self.channel

    def is_server_msg(self, msg):
        return msg.sender == self.ident

    def is_own_msg(self, msg):
        return msg.sender == self.nick

    def process_own_msg(self, msg):
        if msg.keyword == 'JOIN':
            logging.info('Now talking in {}.'.format(msg.text))

    def process_query(self, msg):
        if msg.sender != OWNER:
            return
        if msg.text == '!quit':
            logging.info('Remote shutdown by {}.'.format(msg.sender))
            sys.exit()

    def process_msg(self, msg):
        if self.is_server_msg(msg):
            self.process_server_msg(msg)
        elif self.is_chan_msg(msg):
            self.process_chan_msg(msg)
        elif self.is_own_msg(msg):
            self.process_own_msg(msg)
        else:
            self.process_query(msg)

    def run(self):
        logging.info('Trying to connect to {}:{}...'.format(
            self.host, self.port))
        for line in self.recv_lines():
            log_input(line)
            msg = Message(line)
            if not self.ident:
                self.ident = msg.sender
            self.process_msg(msg)
