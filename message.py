#!/usr/bin/python


class Message(object):
    def __init__(self, line):
        self.line = line
        self._sender = None
        self._text = None
        self._keyword = None
        self._channel = None

    @property
    def sender(self):
        if not self._sender:
            user = self.line.split()[0][1:]
            self._sender = user.split('!')[0]
        return self._sender

    @property
    def channel(self):
        if not self._channel:
            self._channel = self.line.split()[2]
        return self._channel

    @property
    def keyword(self):
        if not self._keyword:
            self._keyword = self.line.split()[1]
        return self._keyword

    @property
    def text(self):
        if not self._text:
            self._text = ''.join(self.line.split(':')[2:])
        return self._text
