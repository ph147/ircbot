#!/usr/bin/python

import random

from time import strftime, sleep
from decorators import action


# TODO function arguments
# TODO outbox queue

def wait_secs():
    n = 5
    sleep(n)
    return 'Waited {} seconds.'.format(n)


def lotto():
    return ', '.join(
        map(str, sorted(random.sample(range(1, 50), 6))))


def get_time():
    return 'Es ist {} Uhr.'.format(strftime("%H:%M:%S"))


@action
def dice_roll():
    return 'rollt eine {}.'.format(random.randrange(1, 7))


ACTIONS = {
    'aspirin': 'gibt {nick} Aspirin.',
}


FUNCS = {
    'time': get_time,
    'dice': dice_roll,
    'roll': dice_roll,
    'lotto': lotto,
    'wait': wait_secs,
}
