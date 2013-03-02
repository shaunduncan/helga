from helga import settings
from helga.extensions import ExtensionRegistry
from helga.log import setup_logger


logger = setup_logger(__name__)


class Helga(object):

    users = {}
    channels = set()
    topics = {}
    client = None
    last_response = {}

    def __init__(self, load=True):
        self.operators = set(getattr(settings, 'OPERATORS', []))
        self.extensions = ExtensionRegistry(bot=self, load=load)

    @property
    def nick(self):
        try:
            return self.client.nickname
        except AttributeError:
            return ''

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
        if not old:
            old = new

        if old not in self.users:
            self.users[new] = set([old])
        else:
            self.users[old].add(new)
            self.users[new] = self.users[old]
            del self.users[old]

    def format_response(self, nick, channel, message):
        resp_fmt = {
            'botnick': self.nick,
            'nick': nick,
            'channel': channel,
            'norm_channel': channel.replace('#', ''),
        }

        return message % resp_fmt

    def on(self, event, *args, **kwargs):
        self.extensions.on(event, *args, **kwargs)

    def process(self, message):
        current_nick = self.nick

        # Some things should go first
        self.extensions.preprocess(message)

        if not message.has_response:
            self.extensions.process(message)

        if message.has_response:
            response = message.format_response(botnick=self.nick)
            self.client.msg(message.resp_channel, response)
            self.last_response[message.resp_channel] = response

        if getattr(settings, 'ALLOW_NICK_CHANGE', False):
            self.client.setNick(current_nick)
