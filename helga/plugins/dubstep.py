import random
import time

from collections import defaultdict

from helga.plugins import match


MAX_WUBS = 3
WUB_TIMEOUT = 10


@match('dubstep', priority=0)
def dubstep(client, channel, nick, message, matches):
    """
    Dubstep can be described as a rapid succession of wub wubs, wow wows, and yep yep yep yeps
    """
    now = time.time()

    if dubstep._last and (now - dubstep._last) > WUB_TIMEOUT:
        dubstep._counts[channel] = 0

    dubstep._last = now
    if dubstep._counts[channel] >= MAX_WUBS:
        dubstep._counts[channel] = 0
        return u'STOP! MY HEAD IS VIBRATING'
    else:
        dubstep._counts[channel] += 1
        return u'wubwub' * dubstep._counts[channel] * random.randint(1, 4)

dubstep._counts = defaultdict(int)
dubstep._last = None
