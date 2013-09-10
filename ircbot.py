#!/usr/bin/python

import sys
import socket
import logging
import config

from connection import Connection
from botcommands import ACTIONS, FUNCS


SERVER_WELCOME = '001'
NICK_USED = '433'

OWNER = 'TheDoctor'


def get_command(msg):
    return msg.split()[0][1:]


def is_command(msg):
    return msg.startswith('!')


class IRCBot(object):
    def __init__(self, host=None, port=None, nick=None, channel=None):
        self.channel = channel or config.CHANNEL
        self.nick = nick or config.NICK
        self.host = host or config.HOST
        self.port = port or config.PORT
        self.connection = Connection(self.host, self.port)
        self.init_dicts()

    def init_dicts(self):
        self.message_types = [
            (self.is_server_msg, self.process_server_msg),
            (self.is_chan_msg, self.process_chan_msg),
            (self.is_own_msg, self.process_own_msg),
        ]
        self.server_messages = {
            SERVER_WELCOME: self.join_channel,
            NICK_USED: self.nick_used,
        }

    def send_credentials(self):
        self.send_nick()
        self.send_user()

    def send(self, text):
        self.connection.send(text)

    def send_user(self):
        self.send('USER my name * * :name')

    def send_nick(self):
        logging.info('Setting nick to {}.'.format(self.nick))
        self.send('NICK {}'.format(self.nick))

    def join_channel(self):
        logging.info('Joining channel {}...'.format(self.channel))
        self.send('JOIN {}'.format(self.channel))

    def channel_msg(self, text, channel=None):
        channel = channel or self.channel
        self.send('PRIVMSG {} {}'.format(channel, text))

    send_query = channel_msg

    def channel_action(self, text):
        self.channel_msg('\x01ACTION {}\x01'.format(text))

    def nick_used(self):
        logging.info('Nick {} already in use.'.format(self.nick))
        self.nick += '_'
        self.send_nick()

    def process_command(self, command, msg):
        if command in ACTIONS:
            self.channel_action(
                ACTIONS[command].format(nick=msg.sender))
        elif command in FUNCS:
            result = FUNCS[command]().format(nick=msg.sender)
            self.channel_msg(result)

    def process_chan_msg(self, msg):
        if is_command(msg.text):
            command = get_command(msg.text)
            self.process_command(command, msg)

    def process_server_msg(self, msg):
        if not self.connection.connected:
            self.connection.connected = True
            self.send_credentials()
        for key in self.server_messages:
            if msg.keyword == key:
                self.server_messages[key]()

    def is_chan_msg(self, msg):
        return msg.keyword == 'PRIVMSG' and msg.channel == self.channel

    def is_server_msg(self, msg):
        return msg.sender == self.connection.ident

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
        for check, process in self.message_types:
            if check(msg):
                process(msg)
                break
        else:
            self.process_query(msg)

    def run(self):
        logging.info('Trying to connect to {}:{}...'.format(
            self.host, self.port))
        for msg in self.connection.recv_messages():
            self.process_msg(msg)
