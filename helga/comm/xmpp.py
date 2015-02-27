import time

from collections import defaultdict

from twisted.internet import protocol, reactor
from twisted.words.xish import domish, xpath
from twisted.words.xish.xmlstream import XmlStreamFactoryMixin
from twisted.words.protocols.jabber import client, jid, xmlstream

import smokesignal

from helga import log, settings
from helga.plugins import registry
from helga.util import encodings


logger = log.getLogger(__name__)


class Factory(XmlStreamFactoryMixin, protocol.ClientFactory):
    """
    XMPP client factory. following :func:`twisted.words.protocols.jabber.client.XMPPClientFactory`.
    Ensures that a client is properly created and handles auto reconnect if helga
    is configured for it (see settings :data:`~helga.settings.AUTO_RECONNECT`
    and :data:`~helga.settings.AUTO_RECONNECT_DELAY`)
    """

    protocol = xmlstream.XmlStream

    def __init__(self):
        if 'JID' in settings.SERVER:
            self.jid = jid.JID(settings.SERVER['JID'])
        else:
            self.jid = jid.JID('{user}@{host}'.format(user=settings.SERVER['USERNAME'],
                                                      host=settings.SERVER['HOST']))
        self.auth = client.XMPPAuthenticator(self.jid, settings.SERVER['PASSWORD'])
        XmlStreamFactoryMixin.__init__(self, self.auth)
        self.client = Client(factory=self)

    def clientConnectionLost(self, connector, reason):
        """
        Handler for when the XMPP connection is lost. Handles auto reconnect if helga
        is configured for it (see settings :data:`~helga.settings.AUTO_RECONNECT` and
        :data:`~helga.settings.AUTO_RECONNECT_DELAY`)
        """
        logger.info('Connection to server lost: %s', reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            delay = getattr(settings, 'AUTO_RECONNECT_DELAY', 5)
            reactor.callLater(delay, connector.connect)
        else:
            raise reason

    def clientConnectionFailed(self, connector, reason):
        """
        Handler for when the XMPP connection fails. Handles auto reconnect if helga
        is configured for it (see settings :data:`~helga.settings.AUTO_RECONNECT` and
        :data:`~helga.settings.AUTO_RECONNECT_DELAY`)
        """
        logger.warning('Connection to server failed: %s', reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            delay = getattr(settings, 'AUTO_RECONNECT_DELAY', 5)
            reactor.callLater(delay, connector.connect)
        else:
            reactor.stop()


class Client(object):
    """
    The XMPP client that has predetermined behavior for certain events.

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

    def __init__(self, factory):
        self.factory = factory
        self.jid = factory.jid
        self.nickname = settings.NICK
        self.stream = None

        # Used for formatting and checking group chat
        if 'MUC_HOST' in settings.SERVER:
            self.conference_host = settings.SERVER['MUC_HOST']
        else:
            self.conference_host = 'conference.{host}'.format(host=settings.SERVER['HOST'])

        # Setup event listeners
        self._bootstrap()

        # Things to keep track of
        self.channels = set()
        self.last_message = defaultdict(dict)  # Dict of x[channel][nick]
        self.channel_loggers = {}

    def _bootstrap(self):
        """
        Bootstraps the client by adding xpath event listeners
        """
        self.factory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.on_connect)
        self.factory.addBootstrap(xmlstream.STREAM_END_EVENT, self.on_disconnect)
        self.factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.on_authenticated)
        self.factory.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.on_init_failed)

        # Listen for chat or groupchat messages
        self.factory.addBootstrap('/message[@type="chat" or @type="groupchat"]', self.on_message)

        # Listen for users leaving the room
        self.factory.addBootstrap('/presence[@type="unavailable"]', self.on_user_left)

        # Listen for users joining the room
        self.factory.addBootstrap('/presence/x/item[@role!="none"]', self.on_user_joined)

        # Allow users to add the bot to their buddy list
        self.factory.addBootstrap('/presence[@type="subscribe"]', self.on_subscribe)

        # Respond to room invites
        self.factory.addBootstrap('/message/x[@xmlns="jabber:x:conference"]', self.on_invite)

        # Handle nick collisions
        self.factory.addBootstrap('/presence/error/conflict', self.on_nick_collision)

    def on_connect(self, stream):
        """
        Handler for a successful connection to the server. Sets the client xml stream
        """
        logger.info('Connection made to %s', settings.SERVER['HOST'])
        self.stream = stream

    def on_disconnect(self, stream):
        """
        Handler for an unexpected disconnect. Simply log and move on
        """
        logger.info('Disconnected from %s', settings.SERVER['HOST'])

    def set_presence(self, presence):
        """
        Sends a presence element to the connected server. Useful for indicating
        online or available status
        """
        el = domish.Element((None, 'presence'))
        el.addElement('status', content=presence)
        self.stream.send(el)

    def on_authenticated(self, stream):
        """
        Handler for successful authentication to the XMPP server. Establishes automatically
        joining channels. Sends the ``signon`` signal (see :ref:`plugins.signals`)
        """
        # Make presence online
        self.set_presence('Online')

        for channel in settings.CHANNELS:
            if isinstance(channel, tuple):
                self.join(*channel)
            else:
                self.join(channel)

    def on_init_failed(self, failure):
        """
        Handler for when client initialization fails. This should end contact with
        the server by sending the xml footer.
        """
        logger.error('Initialization failed: %s', failure)
        self.stream.sendFooter()

    def get_channel_logger(self, channel):
        """
        Gets a channel logger, keeping track of previously requested ones.
        (see :ref:`builtin.channel_logging`)

        :param str channel: A channel name
        """
        if channel not in self.channel_loggers:
            self.channel_loggers[channel] = log.get_channel_logger(channel)
        return self.channel_loggers[channel]

    def log_channel_message(self, channel, nick, message):
        """
        Logs one or more messages by a user on a channel using a channel logger.
        If channel logging is not enabled, nothing happens. (see :ref:`builtin.channel_logging`)

        :param str channel: A channel name
        :param str nick: The nick of the user sending an IRC message
        :param str message: The IRC message
        """
        if not settings.CHANNEL_LOGGING:
            return
        chan_logger = self.get_channel_logger(channel)
        chan_logger.info(message, extra={'nick': nick})

    def joined(self, channel):
        """
        Called when the client successfully joins a new channel. Adds the channel to the known
        channel list and sends the ``join`` signal (see :ref:`plugins.signals`)

        :param str channel: the channel that has been joined
        """
        logger.info('Joined %s', channel)
        self.channels.add(channel)
        smokesignal.emit('join', self, channel)

    def left(self, channel):
        """
        Called when the client successfully leaves a channel. Removes the channel from the known
        channel list and sends the ``left`` signal (see :ref:`plugins.signals`)

        :param str channel: the channel that has been left
        """
        logger.info('Left %s', channel)
        self.channels.discard(channel)
        smokesignal.emit('left', self, channel)

    def parse_nick(self, message):
        """
        Parses a nick from a full XMPP jid. This will also take special care to parse a nick
        as a user jid or a resource from a room jid. For example from ``me@jabber.local``
        would return ``me`` and ``bots@conference.jabber.local/me`` would return ``me``.

        :param message: A <message/> element, instance of :class:`twisted.words.xish.domish.Element`
        :returns: The nick portion of the XMPP jid
        """
        from_jid = jid.JID(message['from'])

        if from_jid.host == self.conference_host:
            return from_jid.resource
        else:
            return from_jid.user

    def parse_channel(self, message):
        """
        Parses a channel name from a message. This follows a few rules to determine the right channel
        to use. Assuming a 'from' jid of user@host/resource:

        * If the type of the message is 'groupchat', the user of the jid is returned with a '#' prefix
        * If the type of the message is 'chat', but the host is the conference host name, the resource
          is returned
        * Otherwise, the user is returned

        :param message: A <message/> element, instance of :class:`twisted.words.xish.domish.Element`
        :returns: The channel portion of the XMPP jid, prefixed with '#' if it's a chat room
        """
        from_jid = jid.JID(message['from'])

        try:
            message_type = message['type']
        except KeyError:
            message_type = ''

        if message_type.lower() == 'groupchat':
            return '#{0}'.format(from_jid.user)
        elif from_jid.host == self.conference_host:
            return from_jid.resource
        else:
            return from_jid.user

    def parse_message(self, message):
        """
        Parses the message body from a <message/> element, ignoring any delayed messages.
        If a message is indeed a delayed message, an empty string is returned

        :param message: A <message/> element, instance of :class:`twisted.words.xish.domish.Element`
        :returns: The contents of the message, empty string if the message is delayed
        """
        if xpath.matches('/message/delay', message):
            return u''
        return xpath.queryForString('/message/body', message)

    def is_public_channel(self, channel):
        """
        Checks if a given channel is public or not. A channel is public if it starts with '#'

        :param str channel: the channel name to check
        """
        return channel.startswith('#')

    def on_message(self, element):
        """
        Handler for an XMPP message. This method handles logging channel messages (if it occurs
        on a public channel) as well as allowing the plugin manager to send the message to all
        registered plugins. Should the plugin manager yield a response, it will be sent back.

        :param message: An XML element for an XMPP <message />
        """
        nick = self.parse_nick(element)
        channel = self.parse_channel(element)
        message = self.parse_message(element)

        # This will be empty for messages that were delayed
        if not message:
            return

        # If we don't ignore this, we'll get infinite replies
        if nick == self.nickname:
            return

        # Log the incoming message and notify message subscribers
        logger.debug('[<--] %s/%s - %s', channel, nick, message)
        is_public = self.is_public_channel(channel)

        # When we get a priv msg, the channel is our current nick, so we need to
        # respond to the user that is talking to us
        if is_public:
            # Only log convos on public channels
            self.log_channel_message(channel, nick, message)
        else:
            channel = nick

        # Some things should go first
        try:
            channel, nick, message = registry.preprocess(self, channel, nick, message)
        except (TypeError, ValueError):
            pass

        # if not message.has_response:
        responses = registry.process(self, channel, nick, message)

        if responses:
            message = u'\n'.join(responses)
            self.msg(channel, message)

            if is_public:
                self.log_channel_message(channel, self.nickname, message)

        # Update last message
        self.last_message[channel][nick] = message

    @encodings.from_unicode_args
    def msg(self, channel, message):
        """
        Send a message over XMPP to the specified channel

        :param channel: The XMPP channel to send the message to. A channel not prefixed by a '#'
                        will be sent as a private message to a user with that nick.
        :param message: The message to send
        """
        logger.debug('[-->] %s - %s', channel, message)
        is_public = self.is_public_channel(channel)

        if is_public:
            resp_host = self.conference_host
            resp_type = 'groupchat'
        else:
            resp_host = self.jid.host
            resp_type = 'chat'

        resp_channel = '{user}@{host}'.format(user=channel, host=resp_host).lstrip('#')

        # Create the response <message/> element
        element = domish.Element(('jabber:client', 'message'))
        element.attributes = {
            'to': resp_channel,
            'from': self.jid.full(),
            'type': resp_type,
        }
        element.addElement('body', content=message)

        self.stream.send(element)

    @encodings.from_unicode_args
    def me(self, channel, message):
        """
        Equivalent to: /me message. This is more compatibility with existing IRC plugins
        that use this method.

        :param channel: The XMPP channel to send the message to. A channel not prefixed by a '#'
                        will be sent as a private message to a user with that nick.
        :param message: The message to send, which will be prefixed with '/me'
        """
        self.msg(channel, '/me {0}'.format(message))

    def on_nick_collision(self, element):
        """
        Handler called when the server responds of nick collision with the bot. This will
        generate a new nick containing the preferred nick and the current timestamp.

        :param element: An XML <presence> element
        """
        channel = jid.JID(element['from']).userhost()

        parts = self.nickname.split('_')
        if len(parts) > 1:
            parts.pop()

        base = '_'.join(parts)
        self.nickname = '{0}_{1}'.join(base, int(time.time()))

        # FIXME: Is this broken? What about the password?
        # See http://xmpp.org/extensions/xep-0045.html#enter-conflict
        self.join(channel)

    def on_invite(self, element):
        """
        Handler that responds to channel invites from other users. This will acknowledge
        the request by joining the room indicated in the xml payload.

        :param element: An XML <message> element containing invite information
        """
        xpath_query = '/message/x[@xmlns="jabber:x:conference"]'
        details = xpath.queryForNodes(xpath_query, element)[0]
        channel = details.attributes['jid']
        password = xpath.queryForString('/message/x/password', element)

        self.join(channel, password=password)

    def on_subscribe(self, element):
        """
        Handler that responds to 'buddy requests' from other users. This will acknowledge
        the request by approving it.

        :param element: An XML <presence> buddy request
        """
        message = domish.Element(('jabber:client', 'presence'))
        message.attributes = {
            'to': element['from'],
            'from': self.jid.full(),
            'type': 'subscribed',
        }
        self.stream.send(message)

    def on_user_joined(self, element):
        """
        Handler called when a user enters a public room. Responsible for sending
        the ``user_joined`` signal (see :ref:`plugins.signals`)

        :param element: An XML <presence> element
        """
        nick = self.parse_nick(element)
        channel = self.parse_channel(element)
        smokesignal.emit('user_joined', self, nick, channel)

    def on_user_left(self, element):
        """
        Handler called when a user leaves a public room. Responsible for sending
        the ``user_left`` signal (see :ref:`plugins.signals`)

        :param element: An XML <presence> element
        """
        nick = self.parse_nick(element)
        channel = self.parse_channel(element)
        smokesignal.emit('user_left', self, nick, channel)

    @encodings.from_unicode_args
    def join(self, channel, password=None):
        """
        Join a channel, optionally with a passphrase required to join.

        :param str channel: the name of the channel to join
        :param str key: an optional passphrase used to join the given channel
        """
        channel = self.format_channel(channel.lstrip('#'))
        logger.info("Joining channel %s", channel)

        element = domish.Element(('jabber:client', 'presence'))
        element.attributes = {
            'to': '{channel}/{nick}'.format(channel=channel, nick=self.nickname),
            'from': self.jid.full(),
        }

        muc = domish.Element(('http://jabber.org/protocol/muc', 'x'))

        if password:
            muc.addElement('password', content=password)

        element.addChild(muc)

        self.stream.send(element)
        self.joined(channel)

    @encodings.from_unicode_args
    def leave(self, channel, reason=None):
        """
        Leave a channel, optionally with a reason for leaving

        :param str channel: the name of the channel to leave
        :param str reason: an optional reason for leaving
        """
        logger.info("Leaving channel %s: %s", channel, reason)
        element = domish.Element(('jabber:client', 'presence'))
        element.attributes = {
            'to': self.format_channel(channel),
            'from': self.jid.full(),
            'type': 'unavailable',
        }
        self.stream.send(element)
        self.left(channel)

    def format_channel(self, channel):
        """
        Format a channel as a JID string. If this channel is already a full
        JID string, then it is returned in the userhost form. Otherwise,
        a string in the form ``{chan}@{host}`` is returned
        """
        channel = channel.lstrip('#')
        fallback = '{channel}@{host}'.format(channel=channel,
                                             host=self.conference_host)

        try:
            channel_jid = jid.JID(channel)
        except jid.InvalidFormat:
            return fallback
        else:
            if channel_jid.user != channel:
                logger.warning('Parsed channel jid %s is invalid', channel_jid.full())
                return fallback
            else:
                return channel_jid.userhost()
