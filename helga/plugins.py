"""
Helga plugins are simple, and there are two types: commands and matches. Command
plugins are meant for asking helga to perform some action (e.g. "helga haiku").
Matches, on the other hand, are meant to provide contextual responses. For example,
if a user mentions "foo", helga may respond with "bar" automatically without having
to be asked to do so specifically. In both cases, responses should be a string. If
a plugin response is None or an empty string, no message will be sent back to the IRC
server.
"""
import re

from functools import partial, wraps


def command(cmd='', aliases=None, help=''):
    """
    Register a method as a helga command. A command is message that you
    ask helga for specifically like "helga haiku".

    :param cmd: The string to invoke this command
    :param aliases: a list of possible aliases for invoking this command
    :param help: help string
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(channel, nick, message):
            pass
        return wrapped
    return decorator


def match(pattern_or_fn=None):
    """
    A match is a type of plugin that will make helga respond if the contents
    of a user's message match a pattern. For example, if a match plugin looks
    for the string "foo", helga will respond with "bar" without being asked
    to do so.

    The only argument to this decorator is either a regular expression or a
    callable. If the argument is a callable, it must accept a single string
    argument, which will be the message that has been received over IRC. By
    convention, this callable should return something that can be checked for
    truthines (i.e. a string, or list of strings).

    The decorated method should accept four arguments:

    - channel: the channel on which the message was received
    - nick: the current nick of the message sender
    - message: the message string itself
    - found: if the decorator argument is a callable, this will be its return value.
      If it is a regex string, this will be the return value of ``re.findall``
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(channel, nick, message):
            if callable(pattern_or_fn):
                matcher = pattern_or_fn
            else:
                matcher = partial(re.findall, pattern_or_fn)

            try:
                found = matcher(message)
            except TypeError:
                # FIXME: Log warning here
                return None

            if not bool(found):
                return None

            try:
                return fn(channel, nick, message, found)
            except TypeError:
                # FIXME: Log warning here
                return None

        return wrapped
    return decorator
