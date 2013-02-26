import time

from twisted.words.protocols import irc

from helga import settings
from helga.bot import Helga
from helga.log import setup_logger


logger = setup_logger(__name__)
helga = Helga()


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

    def joined(self, channel):
        logger.info('Joined %s' % channel)
        helga.join_channel(channel)

    def parse_nick(self, full_nick):
        """
        Parses a full IRC nick like {nick}!~{user}@{host}
        """
        return full_nick.split('!')[0]

    def setNick(self, nickname):
        self._attemptedNick = nickname

        msg = 'NICK %s' % nickname
        self._reallySendLine(msg)

    def is_public_channel(self, channel):
        return self.nickname != channel

    def privmsg(self, user, channel, message):
        user = self.parse_nick(user)
        message = message.strip()

        logger.debug('[<--] %s/%s - %s' % (channel, user, message))

        helga.handle_message(user, channel, message, self.is_public_channel(channel))

    def user_renamed(self, oldnick, newnick):
        logger.debug('User %s is now known as %s' % (oldnick, newnick))
        helga.update_user_nick(oldnick, newnick)

    def alterCollidedNick(self, nickname):
        """
        Returns timestamp appended nick
        """
        logger.info('Nick %s already taken' % nickname)
        stripped = '_'.join(self.nickname.split('_')[:-1])
        self.nickname = '%s_%d' % (stripped, time.time())

        return self.nickname

    def kickedFrom(self, channel, kicker, message):
        logger.warning('%s kicked bot from %s: %s' % (kicker, channel, message))
        helga.leave_channel(channel)

    def userJoined(self, user, channel):
        user = self.parse_nick(user)
        logger.info('%s joined %s' % (user, channel))
        helga.update_user_nick(user, user)

    def userLeft(self, user, channel):
        user = self.parse_nick(user)
        logger.info('%s left %s' % (user, channel))

    def userQuit(self, user, quitMessage):
        user = self.parse_nick(user)
        logger.info('%s disconnected' % user)

    def topicUpdated(self, user, channel, topic):
        user = self.parse_nick(user)
        logger.info('%s set topic on %s to: %s' % (user, channel, topic))
        helga.set_topic(channel, topic)

    def msg(self, channel, message):
        logger.debug('[-->] %s - %s' % (channel, message))
        irc.IRCClient.msg(self, channel, str(message))
