import time

from collections import defaultdict

import smokesignal

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc

from helga import settings, log
from helga.plugins.core import registry
from helga.util import encodings


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
        logger.info('Connection to server lost: %s', reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            delay = getattr(settings, 'AUTO_RECONNECT_DELAY', 5)
            reactor.callLater(delay, connector.connect)
        else:
            raise reason

    def clientConnectionFailed(self, connector, reason):
        logger.warning('Connection to server failed: %s', reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            delay = getattr(settings, 'AUTO_RECONNECT_DELAY', 5)
            reactor.callLater(delay, connector.connect)
        else:
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
    encoding = 'UTF-8'

    def __init__(self, factory=None):
        self.factory = factory

        # Pre-configured helga admins
        self.operators = set(getattr(settings, 'OPERATORS', []))

        # Things to keep track of
        self.channels = set()
        self.last_message = defaultdict(dict)  # Dict of x[channel][nick]

    def connectionMade(self):
        logger.info('Connection made to %s', settings.SERVER['HOST'])
        irc.IRCClient.connectionMade(self)

    @encodings.from_unicode_args
    def connectionLost(self, reason):
        logger.info('Connection to %s lost: %s', settings.SERVER['HOST'], reason)
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in settings.CHANNELS:
            # If channel is more than one item tuple, second value is password
            if len(channel) > 1:
                self.join(encodings.from_unicode(channel[0]),
                          encodings.from_unicode(channel[1]))
            else:
                self.join(encodings.from_unicode(channel[0]))
        smokesignal.emit('signon', self)

    def joined(self, channel):
        logger.info('Joined %s', channel)
        self.channels.add(channel)
        smokesignal.emit('join', self, channel)

    def left(self, channel):
        logger.info('Left %s', channel)
        self.channels.discard(channel)
        smokesignal.emit('left', self, channel)

    def parse_nick(self, full_nick):
        """
        Parses a full IRC nick like {nick}!~{user}@{host}
        """
        return full_nick.split('!')[0]

    def is_public_channel(self, channel):
        return self.nickname != channel

    @encodings.to_unicode_args
    def privmsg(self, user, channel, message):
        user = self.parse_nick(user)
        message = message.strip()

        logger.debug('[<--] %s/%s - %s', channel, user, message)

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
        logger.info('Nick %s already taken', nickname)

        parts = nickname.split('_')
        if len(parts) > 1:
            parts = parts[:-1]

        stripped = '_'.join(parts)
        self.nickname = '{0}_{1}'.format(stripped, time.time())

        return self.nickname

    def kickedFrom(self, channel, kicker, message):
        logger.warning('%s kicked bot from %s: %s', kicker, channel, message)
        self.channels.discard(channel)

    @encodings.from_unicode_args
    def msg(self, channel, message):
        logger.debug('[-->] %s - %s', channel, message)
        irc.IRCClient.msg(self, channel, message)

    def on_invite(self, inviter, invitee, channel):
        nick = self.parse_nick(inviter)
        if invitee == self.nickname:
            logger.info('%s invited %s to %s', nick, invitee, channel)
            self.join(channel)

    def irc_unknown(self, prefix, command, params):
        """
        Handle any unknown things...like INVITE
        """
        if command.lower() == 'invite':
            self.on_invite(prefix, params[0], params[1])

    @encodings.from_unicode_args
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

    @encodings.from_unicode_args
    def join(self, channel, key=None):
        """
        Join a channel. Override to handle accepting unicode arguments.
        """
        logger.info("Joining channel %s", channel)
        irc.IRCClient.join(self, channel, key=key)

    @encodings.from_unicode_args
    def leave(self, channel, reason=None):
        """
        Leave a channel. Override to handle accepting unicode arguments.
        """
        logger.info("Leaving channel %s: %s", channel, reason)
        irc.IRCClient.leave(self, channel, reason=reason)
