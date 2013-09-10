#!/usr/bin/python


def action(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return '\x01ACTION {}\x01'.format(result)
    return wrapper
