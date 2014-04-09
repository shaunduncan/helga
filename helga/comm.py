import time

from collections import defaultdict

import smokesignal

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc

from helga import settings, log
from helga.plugins.core import registry


logger = log.getLogger(__name__)


class Factory(protocol.ClientFactory):
    """
    The client factory for twisted. Does little more than add in some logging along the
    way and make sure the client is properly created. Also handles auto reconnect if it
    is configured in settings.
    """

    def buildProtocol(self, address):
        logger.debug('Constructing Helga protocol')
        return Client(factory=self)

    def clientConnectionLost(self, connector, reason):
        logger.info('Connection to server lost: {0}'.format(reason))

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            connector.connect()
        else:
            raise reason

    def clientConnectionFailed(self, connector, reason):
        logger.warning('Connection to server failed: {0}'.format(reason))
        reactor.stop()


class Client(irc.IRCClient):
    """
    Implementation of twisted IRCClient using settings as overrides for default
    values. Some methods are subclassed here only to provide logging output.
    """

    nickname = settings.NICK

    # Server related things
    username = settings.SERVER.get('USERNAME', None)
    password = settings.SERVER.get('PASSWORD', None)

    # Other confg
    lineRate = getattr(settings, 'RATE_LIMIT', None)
    sourceURL = 'http://github.com/shaunduncan/helga'
    encode = 'UTF-8'

    def __init__(self, factory=None):
        self.factory = factory

        # Pre-configured helga admins
        self.operators = set(getattr(settings, 'OPERATORS', []))

        # Things to keep track of
        self.channels = set()
        self.last_message = defaultdict(dict)  # Dict of x[channel][nick]

    def connectionMade(self):
        logger.info('Connection made to {0}'.format(settings.SERVER['HOST']))
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        logger.info('Connection to {0} lost'.format(settings.SERVER['HOST']))
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in settings.CHANNELS:
            if len(channel) > 1:
                self.join(channel[0], channel[1])
            else:
                self.join(channel[0])
        smokesignal.emit('signon', self)

    def joined(self, channel):
        logger.info('Joined {0}'.format(channel))
        self.channels.add(channel)
        smokesignal.emit('join', self, channel)

    def left(self, channel):
        logger.info('Joined {0}'.format(channel))
        self.channels.discard(channel)
        smokesignal.emit('left', self, channel)

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

        logger.debug(u'[<--] {0}/{1} - {2}'.format(channel, user, message))

        # When we get a priv msg, the channel is our current nick, so we need to
        # respond to the user that is talking to us
        channel = channel if self.is_public_channel(channel) else user

        # Some things should go first
        try:
            channel, user, message = registry.preprocess(self, channel, user, message)
        except (TypeError, ValueError):
            pass

        # if not message.has_response:
        responses = registry.process(self, channel, user, message)

        if responses:
            self.msg(channel, '\n'.join(responses))

        # Update last message
        self.last_message[channel][user] = message

    def alterCollidedNick(self, nickname):
        """
        Returns timestamp appended nick
        """
        logger.info('Nick {0} already taken'.format(nickname))

        parts = nickname.split('_')
        if len(parts) > 1:
            parts = parts[:-1]

        stripped = '_'.join(parts)
        self.nickname = '{0}_{1}'.format(stripped, time.time())

        return self.nickname

    def kickedFrom(self, channel, kicker, message):
        logger.warning('{0} kicked bot from {1}: {2}'.format(kicker, channel, message))
        self.channels.discard(channel)

    def msg(self, channel, message):
        logger.debug(u'[-->] {0} - {1}'.format(channel, message))
        irc.IRCClient.msg(self, channel, message.encode('UTF-8'))

    def on_invite(self, inviter, invitee, channel):
        nick = self.parse_nick(inviter)
        if invitee == self.nickname:
            logger.info('{0} invited {1} to {2}'.format(nick, invitee, channel))
            self.join(channel)

    def irc_unknown(self, prefix, command, params):
        """
        Handle any unknown things...like INVITE
        """
        if command.lower() == 'invite':
            self.on_invite(prefix, params[0], params[1])

    def me(self, channel, message):
        """
        A proxy for the WTF-named method `describe`. Basically the same as doing `/me waves`
        """
        irc.IRCClient.describe(self, channel, message)

    def userJoined(self, user, channel):
        """
        Send a signal when a user has joined a channel
        """
        nick = self.parse_nick(user)
        smokesignal.emit('user_joined', self, nick, channel)

    def userLeft(self, user, channel):
        """
        Send a signal when a user has left a channel
        """
        nick = self.parse_nick(user)
        smokesignal.emit('user_left', self, nick, channel)
