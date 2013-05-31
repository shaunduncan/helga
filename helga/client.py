import time

import smokesignal
from twisted.words.protocols import irc

from helga import settings
from helga.bot import Helga
from helga.log import setup_logger


logger = setup_logger(__name__)
helga = Helga()


class Message(object):
    """
    Just creates a dict of things that is passed around to helga's internals
    """

    def __init__(self, from_nick, channel, message, is_public):
        self.from_nick = from_nick
        self.on_channel = channel
        self.resp_channel = channel if is_public else from_nick
        self.is_public = is_public
        self.message = message
        self.response = []  # support multi-line responses

    def format_response(self, **kwargs):
        response = self.response
        resp_fmt = {
            'nick': self.from_nick,
            'channel': self.on_channel,
            'norm_channel': self.on_channel.replace('#', ''),
        }

        # plus any kwargs
        resp_fmt.update(kwargs)

        if isinstance(response, list):
            response = '\n'.join(response)

        return response % resp_fmt

    @property
    def channel(self):
        # Will always be the right channel
        return self.resp_channel

    @property
    def has_response(self):
        return True if self.response else False


class HelgaClient(irc.IRCClient):

    nickname = getattr(settings, 'DEFAULT_NICK', 'helga')

    # Server related things
    username = settings.SERVER.get('USERNAME', None)
    password = settings.SERVER.get('PASSWORD', None)

    # Other confg
    lineRate = getattr(settings, 'RATE_LIMIT', None)
    sourceURL = 'http://github.com/shaunduncan/helga'
    encode = 'UTF-8'

    def connectionMade(self):
        logger.info('Connection made to %s' % settings.SERVER['HOST'])
        irc.IRCClient.connectionMade(self)
        helga.client = self

    def connectionLost(self, reason):
        logger.info('Connection to %s lost' % settings.SERVER['HOST'])
        irc.IRCClient.connectionLost(self, reason)
        helga.client = None

    def signedOn(self):
        for channel in settings.CHANNELS:
            self.join(channel)

        # Hook FTW
        smokesignal.emit('signon')

    def joined(self, channel):
        logger.info('Joined %s' % channel)
        helga.join_channel(channel)
        smokesignal.emit('join', channel)

    def parse_nick(self, full_nick):
        """
        Parses a full IRC nick like {nick}!~{user}@{host}
        """
        return full_nick.split('!')[0]

    def is_public_channel(self, channel):
        return self.nickname != channel

    def privmsg(self, user, channel, message):
        user = self.parse_nick(user)
        message = message.strip()

        logger.debug('[<--] %s/%s - %s' % (channel, user, message))

        msg = Message(user, channel, message, self.is_public_channel(channel))
        helga.process(msg)

    def user_renamed(self, oldnick, newnick):
        logger.debug('User %s is now known as %s' % (oldnick, newnick))
        helga.update_user_nick(oldnick, newnick)

    def alterCollidedNick(self, nickname):
        """
        Returns timestamp appended nick
        """
        logger.info('Nick %s already taken' % nickname)

        parts = nickname.split('_')
        if len(parts) > 1:
            parts = parts[:-1]

        stripped = '_'.join(parts)
        self.nickname = '%s_%d' % (stripped, time.time())

        return self.nickname

    def kickedFrom(self, channel, kicker, message):
        logger.warning('%s kicked bot from %s: %s' % (kicker, channel, message))
        helga.leave_channel(channel)

    def userJoined(self, user, channel):
        user = self.parse_nick(user)
        logger.debug('%s joined %s' % (user, channel))
        helga.update_user_nick(user, user)

    def msg(self, channel, message):
        logger.debug('[-->] %s - %s' % (channel, message))
        irc.IRCClient.msg(self, channel, message.encode('UTF-8'))

    def on_invite(self, inviter, invitee, channel):
        nick = self.parse_nick(inviter)
        if invitee == self.nickname:
            logger.info('%s invited %s to %s' % (nick, invitee, channel))
            self.join(channel)

    def irc_unknown(self, prefix, command, params):
        """
        Handle any unknown things...like INVITE
        """
        if command.lower() == 'invite':
            self.on_invite(prefix, params[0], params[1])

    def me(self, channel, message):
        """
        A proxy for the WTF-named method `describe`. Basically the same as doing
        /me waves
        """
        irc.IRCClient.describe(self, channel, message)
