import time

from collections import defaultdict

import smokesignal

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc

from helga import plugins, settings, log


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
        logger.info('Connection to server lost: %s' % reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            connector.connect()
        else:
            raise reason

    def clientConnectionFailed(self, connector, reason):
        logger.warning('Connection to server failed: %s' % reason)
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
        logger.info('Connection made to %s' % settings.SERVER['HOST'])
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        logger.info('Connection to %s lost' % settings.SERVER['HOST'])
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in settings.CHANNELS:
            if len(channel) > 1:
                self.join(channel[0], channel[1])
            else:
                self.join(channel[0])
        smokesignal.emit('signon')

    def joined(self, channel):
        logger.info('Joined %s' % channel)
        self.channels.add(channel)
        smokesignal.emit('join', channel)

    def left(self, channel):
        logger.info('Joined %s' % channel)
        self.channels.discard(channel)
        smokesignal.emit('left', channel)

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

        # When we get a priv msg, the channel is our current nick, so we need to
        # respond to the user that is talking to us
        channel = channel if self.is_public_channel(channel) else user

        # Some things should go first: FIXME
        # channel, nick, message = plugins.registry.pre_process(self, channel, nick, message)

        # if not message.has_response:
        responses = plugins.registry.process(self, channel, user, message)

        if responses:
            # FIXME: Should have a setting to only allow a single response
            self.msg(channel, '\n'.join(responses))

        # Update last message
        self.last_message[channel][user] = message

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
        self.channels.discard(channel)

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
        A proxy for the WTF-named method `describe`. Basically the same as doing `/me waves`
        """
        irc.IRCClient.describe(self, channel, message)
