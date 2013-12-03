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

from functools import wraps


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
        def wrapped(channel, nick, message, channel_is_public):
            pass
        return wrapped
    return decorator


def match(pattern_or_fn=None, response_or_fn=None):
    """
    A match is a type of plugin that will make helga respond if the contents
    of a user's message match a pattern. For example, if a match plugin looks
    for the string "foo", helga will respond with "bar" without being asked
    to do so.

    :param pattern_or_fn: either a regular expression or a callable that accepts
                          a string and returns a boolean if there is a match. If
                          this argument is a callable, it must accept four args:
                              - channel: the channel the message was sent on
                              - nick: the current nick of the user sending the message
                              - message: the raw message sent by the user
                              - channel_is_public: boolean, True if channel is public
    :param response_or_fn: either a string or a callable that returns a string response.
                           If this argument is a callable, it must accept no arguments
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(channel, nick, message, channel_is_public):
            if callable(pattern_or_fn):
                try:
                    should_respond = pattern_or_fn(channel, nick, message, channel_is_public)
                except TypeError:
                    # FIXME: Log warning here
                    return u''
            else:
                should_respond = bool(re.findall(pattern_or_fn, message))

            if not should_respond:
                return u''

            return response_or_fn() if callable(response_or_fn) else response_or_fn
        return wrapped
    return decorator
