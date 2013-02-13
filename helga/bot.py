import random

from helga import settings
from helga.extensions import extensions
from helga.extensions.stfu import stfu
from helga.log import setup_logger


logger = setup_logger(__name__)


class Helga(object):

    users = {}
    channels = set()
    silence = set()  # Like channels, but a list of quietness
    topics = {}
    client = None

    def __init__(self):
        self.operators = set(getattr(settings, 'OPERATORS', []))

    @property
    def nick(self):
        return self.client.nickname

    def set_topic(self, channel, topic):
        self.topics[channel] = topic

    def join_channel(self, channel):
        self.channels.add(channel)

    def leave_channel(self, channel):
        self.channels.discard(channel)

    def get_current_nick(self, nick):
        if nick in self.users:
            return nick

        # Otherwise, try to figure out if it's stale
        for current, past in self.users.iteritems():
            if nick in past:
                return current

        # Otherwise, it's current
        return nick

    def update_user_nick(self, old, new):
        if old not in self.users:
            self.users[new] = set([old])
        else:
            self.users[old].discard(old)
            self.users[new] = self.users[old]
            del self.users[old]

    def handle_message(self, nick, channel, message, is_public):
        # We should pre-dispatch stfu commands
        response = stfu.dispatch(self, nick, channel, message, is_public)

        if not stfu.is_silenced(channel):
            response = extensions.dispatch(self, nick, channel, message, is_public)

        if response:
            resp_channel = channel if is_public else nick
            resp_fmt = {
                'botnick': self.nick,
                'nick': nick,
                'channel': channel,
            }

            self.client.msg(resp_channel, str(response % resp_fmt))


helga = Helga()
