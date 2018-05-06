"""
Base implementations for comm clients
"""

from collections import defaultdict

from helga import settings


class BaseClient(object):
    """
    A base client implementation for any arbitrary protocol. Manages keeping track of global
    settings needed for core functionality as well as other general client state.

    .. attribute:: channels
        :annotation: = set()

        A set containing all of the channels the bot is currently in

    .. attribute:: operators
        :annotation: = set()

        A set containing all of the configured operators (setting :data:`~helga.settings.OPERATORS`)

    .. attribute:: last_message
        :annotation: = dict()

        A channel keyed dictionary containing dictionaries of nick -> message of the last messages
        the bot has seen a user send on a given channel. For instance, if in the channel ``#foo``::

            <sduncan> test

        The contents of this dictionary would be::

            self.last_message['#foo']['sduncan'] = 'test'

    .. attribute:: channel_loggers
        :annotation: = dict()

        A dictionary of known channel loggers, keyed off the channel name
    """

    def __init__(self):
        # Pre-configured helga admins
        self.operators = set(getattr(settings, 'OPERATORS', []))

        # Things to keep track of
        self.channels = set()
        self.last_message = defaultdict(dict)  # Dict of x[channel][nick]
        self.channel_loggers = {}

    # TODO: fill in the base methods so we can do appropriate tracking
