from helga import settings
from helga.extensions import ExtensionRegistry
from helga.log import setup_logger


logger = setup_logger(__name__)


class Helga(object):

    users = {}
    channels = set()
    topics = {}
    client = None

    def __init__(self, load=True):
        self.operators = set(getattr(settings, 'OPERATORS', []))
        self.extensions = ExtensionRegistry(bot=self, load=load)

        # STFU might depend on importing this module
        from helga.extensions.stfu import STFUExtension
        self.stfu = STFUExtension(bot=self)

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

    def handle_message(self, nick, channel, message, is_public):
        # We should pre-dispatch stfu commands
        response = self.stfu.dispatch(self, nick, channel, message, is_public)

        if not self.stfu.is_silenced(channel) and not response:
            response = self.extensions.dispatch(self, nick, channel, message, is_public)

        if response:
            resp_channel = channel if is_public else nick
            resp_fmt = {
                'botnick': self.nick,
                'nick': nick,
                'channel': channel,
            }

            self.client.msg(resp_channel, str(response % resp_fmt))
