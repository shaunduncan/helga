import time
import uuid

from collections import defaultdict

from twisted.internet import protocol, reactor, task
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
    XMPP client factory. following `twisted.words.protocols.jabber.client.XMPPClientFactory`.
    Ensures that a client is properly created and handles auto reconnect if helga
    is configured for it (see settings :data:`~helga.settings.AUTO_RECONNECT`
    and :data:`~helga.settings.AUTO_RECONNECT_DELAY`).

    By default the Jabber ID is set using the form ``USERNAME@HOST`` from :data:`~helga.settings.SERVER`,
    but a specific value can be used with the ``JID`` key instead.

    .. attribute:: jid

        The Jabber ID used by the client. Configured directly via ``JID`` in :data:`~helga.settings.SERVER`
        or indirectly as ``USERNAME@HOST`` from :data:`~helga.settings.SERVER`. An instance of
        `twisted.words.protocols.jabber.jid.JID`.

    .. attribute:: auth

        An instance of `twisted.words.protocols.jabber.client.XMPPAuthenticator` used for
        password authentication of the server connection.

    .. attribute:: client

        The client instance of :class:`Client`
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

        :param connector: The twisted conntector
        :param reason: A twisted Failure instance
        :raises: The given reason unless AUTO_RECONNECT is enabled
        """
        logger.error('Connection to server lost: %s', reason)

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

        :param connector: The twisted conntector
        :param reason: A twisted Failure instance
        :raises: The given reason unless AUTO_RECONNECT is enabled
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
    The XMPP client that has predetermined behavior for certain events. This client assumes
    some default behavior for multi user chat (MUC) by setting the conference host as
    ``conference.HOST`` using ``HOST`` in :data:`~helga.settings.SERVER`. A specific MUC host
    can be specified using the key ``MUC_HOST`` in :data:`~helga.settings.SERVER`.

    This client is also a bit opinionated when it comes to chat rooms and how room names and nicks
    are delivered to plugins. Since helga originally started as an IRC bot, channels are sent
    to plugins as the user portion of the room JID prefixed with '#'. For example, if a message
    is received from ``bots@conference.example.com/some_user``, the channel will be ``#bots``.
    In this instance, plugins would see the user nick as ``some_user``. For private messages,
    a message received from ``some_user@example.com`` would result in an identical channel and
    nick ``some_user``.

    .. attribute:: factory

        An instance of :class:`Factory` used to create this client instance.

    .. attribute:: jid

        The Jabber ID used by the client. A copy of the factory ``jid`` attribute.

    .. attribute:: nickname

        The current nickname of the bot. Generally this is the user portion of the ``jid`` attribute,
        and the resource portion of chat room JIDs, but the value is obtained via the setting
        :data:`~helga.settings.NICK`. For HipChat support, this should be set to the user account's
        **Full Name**.

    .. attribute:: stream

        The raw data stream. An instance of `twisted.words.protocols.jabber.xmlstream.XmlStream`

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

        # Pre-configured helga admins
        self.operators = set(getattr(settings, 'OPERATORS', []))

        # Things to keep track of
        self.channels = set()
        self.last_message = defaultdict(dict)  # Dict of x[channel][nick]
        self.channel_loggers = {}
        self._heartbeat = None

    def _bootstrap(self):
        """
        Bootstraps the client by adding xpath event listeners. Listeners include

        - on_connect: when the server connection is established and the stream is opened
        - on_disconnect: when the server connection is terminated and the stream is closed
        - on_authenticated: when the client is succesfully authenticated
        - on_init_failed: when a failure occurs initializing the client
        - on_message: when a private or group chat message is received
        - on_user_left: when a user has left a chat room
        - on_user_joined: when a user joins a chat room
        - on_subscribe: when a user wants to add the bot as a buddy
        - on_invite: when the bot is invited to a chat room
        - on_nick_collision: when the server informs the bot of a nick collision in a chat room
        - on_ping: when the server or another user pings the bot
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

        # Respond to room invites, mediated and direct
        self.factory.addBootstrap('/message/x', self.on_invite)

        # Handle nick collisions
        self.factory.addBootstrap('/presence/error/conflict', self.on_nick_collision)

        # Handle server pings, prevents unexpected disconnects
        self.factory.addBootstrap('/iq/ping', self.on_ping)

    def _start_heartbeat(self):
        """
        Starts a PING looping call that operates as a heartbeat/keepalive mechanism for the client.
        Effectively sends an IQ PING to the XMPP server once every 60 seconds.
        """
        self._stop_heartbeat()

        logger.info('Starting PING heartbeat task')
        self._heartbeat = task.LoopingCall(self.ping)
        self._heartbeat .start(60, now=False)

    def _stop_heartbeat(self):
        """
        Stops the IQ PING heartbeat service if it exists and is running
        """
        if self._heartbeat is not None:
            logger.info('Stopping PING heartbeat task')
            self._heartbeat.stop()
            self._heartbeat = None

    def ping(self):
        """
        Sends an IQ PING to the host server. Useful for establishing a heartbeat/keepalive
        """
        logger.debug('Sending PING to %s', settings.SERVER['HOST'])

        ping = domish.Element(('', 'iq'), attribs={
            'id': str(uuid.uuid4()),
            'from': self.jid.full(),
            'to': settings.SERVER['HOST'],
            'type': 'get',
        })
        ping.addElement('ping', 'urn:xmpp:ping')
        self.stream.send(ping)

    def on_ping(self, el):
        """
        Handler for server IQ pings. Automatically responds back with a PONG.

        :param el: A <iq/> PING message, instance of `twisted.words.xish.domish.Element`
        """
        logger.debug('Received PING from %s', el['from'])
        pong = domish.Element(('', 'iq'), attribs={
            'id': el['id'],
            'to': el['from'],
            'from': el['to'],
            'type': 'result',
        })
        self.stream.send(pong)

    def on_connect(self, stream):
        """
        Handler for a successful connection to the server. Sets the client xml stream and
        starts the heartbeat service.

        :param stream: An instance of `twisted.words.protocols.jabber.xmlstream.XmlStream`
        """
        logger.info('Connection made to %s', settings.SERVER['HOST'])
        self.stream = stream
        self._start_heartbeat()

    def on_disconnect(self, stream):
        """
        Handler for an unexpected disconnect. Logs the disconnect and stops the heartbeat service.

        :param stream: An instance of `twisted.words.protocols.jabber.xmlstream.XmlStream`
        """
        logger.info('Disconnected from %s', settings.SERVER['HOST'])
        self._stop_heartbeat()

    def set_presence(self, presence):
        """
        Sends a <presence/> element to the connected server. Used to indicate online or available status

        :param presence: The presence status string to send to the server
        """
        el = domish.Element((None, 'presence'))
        el.addElement('status', content=presence)
        self.stream.send(el)

    def on_authenticated(self, stream):
        """
        Handler for successful authentication to the XMPP server. Establishes automatically
        joining channels. Sends the ``signon`` signal (see :ref:`plugins.signals`)

        :param stream: An instance of `twisted.words.protocols.jabber.xmlstream.XmlStream`
        """
        # Make presence online
        self.set_presence('Online')

        for channel in settings.CHANNELS:
            if isinstance(channel, tuple):
                self.join(*channel)
            else:
                self.join(channel)

        smokesignal.emit('signon', self)

    def on_init_failed(self, failure):
        """
        Handler for when client initialization fails. This should end contact with
        the server by sending the xml footer.

        :param failure: The element of the failure
        """
        logger.error('Initialization failed: %s', failure)
        self.stream.sendFooter()

    def get_channel_logger(self, channel):
        """
        Gets a channel logger, keeping track of previously requested ones.
        (see :ref:`builtin.channel_logging`)

        :param channel: A channel name
        :returns: a python logger suitable for channel logging
        """
        if channel not in self.channel_loggers:
            self.channel_loggers[channel] = log.get_channel_logger(channel)
        return self.channel_loggers[channel]

    def log_channel_message(self, channel, nick, message):
        """
        Logs one or more messages by a user on a channel using a channel logger.
        If channel logging is not enabled, nothing happens. (see :ref:`builtin.channel_logging`)

        :param channel: A channel name
        :param nick: The nick of the user sending an IRC message
        :param message: The IRC message
        """
        if not settings.CHANNEL_LOGGING:
            return
        chan_logger = self.get_channel_logger(channel)
        chan_logger.info(message, extra={'nick': nick})

    def joined(self, channel):
        """
        Called when the client successfully joins a new channel. Adds the channel to the known
        channel list and sends the ``join`` signal (see :ref:`plugins.signals`)

        :param channel: the channel that has been joined
        """
        logger.info('Joined %s', channel)
        self.channels.add(channel)
        smokesignal.emit('join', self, channel)

    def left(self, channel):
        """
        Called when the client successfully leaves a channel. Removes the channel from the known
        channel list and sends the ``left`` signal (see :ref:`plugins.signals`)

        :param channel: the channel that has been left
        """
        logger.info('Left %s', channel)
        self.channels.discard(channel)
        smokesignal.emit('left', self, channel)

    def parse_nick(self, message):
        """
        Parses a nick from a full XMPP jid. This will also take special care to parse a nick
        as a user jid or a resource from a room jid. For example from ``me@jabber.local``
        would return ``me`` and ``bots@conference.jabber.local/me`` would return ``me``.

        :param message: A <message/> element, instance of `twisted.words.xish.domish.Element`
        :returns: The nick portion of the XMPP jid
        """
        from_jid = jid.JID(message['from'])

        if from_jid.host == self.conference_host:
            return from_jid.resource
        else:
            return from_jid.user

    def parse_channel(self, element):
        """
        Parses a channel name from an element. This follows a few rules to determine the right channel
        to use. Assuming a 'from' jid of ``user@host/resource``:

        * If the element tag is 'presence', the user portion of the jid is returned with '#' prefix
        * If the element type is 'groupchat', the user portion of the jid is returned with a '#' prefix
        * If the element type is 'chat', but the host is the conference host name, the resource
          portion of the jid is returned
        * Otherwise, the user portion of the jid is returned

        :param element: An instance of `twisted.words.xish.domish.Element`
        :returns: The channel portion of the XMPP jid, prefixed with '#' if it's a chat room
        """
        from_jid = jid.JID(element['from'])

        try:
            element_type = element['type']
        except KeyError:
            element_type = ''

        if element_type.lower() == 'groupchat' or element.name == 'presence':
            return '#{0}'.format(from_jid.user)
        elif from_jid.host == self.conference_host:
            return from_jid.resource
        else:
            return from_jid.user

    def parse_message(self, message):
        """
        Parses the message body from a <message/> element, ignoring any delayed messages.
        If a message is indeed a delayed message, an empty string is returned

        :param message: A <message/> element, instance of `twisted.words.xish.domish.Element`
        :returns: The contents of the message, empty string if the message is delayed
        """
        if xpath.matches('/message/delay', message):
            return u''

        # This is a hack around a unicode bug in twisted queryForString
        strings = xpath.queryForStringList('/message/body', message)
        if strings:
            return strings[0]
        return u''

    def is_public_channel(self, channel):
        """
        Checks if a given channel is public or not. A channel is public if it starts with '#'

        :param channel: the channel name to check
        """
        return channel.startswith('#')

    def on_message(self, element):
        """
        Handler for an XMPP message. This method handles logging channel messages (if it occurs
        on a public channel) as well as allowing the plugin manager to send the message to all
        registered plugins. Should the plugin manager yield a response, it will be sent back.

        :param message: A <message/> element, instance of `twisted.words.xish.domish.Element`
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
        Send a message over XMPP to the specified channel. Channels prefixed with '#' are assumed
        to be multi user chat rooms, otherwise, they are assumed to be individual users.

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
        element = domish.Element(('jabber:client', 'message'), attribs={
            'to': resp_channel,
            'from': self.jid.full(),
            'type': resp_type,
        })
        element.addElement('body', content=encodings.to_unicode(message))

        self.stream.send(element)

    @encodings.from_unicode_args
    def me(self, channel, message):
        """
        Equivalent to: /me message. This is more compatibility with existing IRC plugins
        that use this method. Channels prefixed with '#' are assumed to be multi user chat
        rooms, otherwise, they are assumed to be individual users.

        :param channel: The XMPP channel to send the message to. A channel not prefixed by a '#'
                        will be sent as a private message to a user with that nick.
        :param message: The message to send, which will be prefixed with '/me'
        """
        self.msg(channel, '/me {0}'.format(message))

    def on_nick_collision(self, element):
        """
        Handler called when the server responds of nick collision with the bot. This will
        generate a new nick containing the preferred nick and the current timestamp and
        attempt to rejoin the room it failed to join.

        :param element: A <presence/> element, instance of `twisted.words.xish.domish.Element`
        """
        channel = jid.JID(element['from']).userhost()

        parts = self.nickname.split('_')
        if len(parts) > 1:
            parts.pop()

        base = '_'.join(parts)
        self.nickname = '{0}_{1}'.format(base, int(time.time()))

        # FIXME: Is this broken? What about the password?
        # See http://xmpp.org/extensions/xep-0045.html#enter-conflict
        self.join(channel)

    def on_invite(self, element):
        """
        Handler that responds to channel invites from other users. This will acknowledge
        the request by joining the room indicated in the xml payload.

        :param element: A <message/> element, instance of `twisted.words.xish.domish.Element`
        """
        channel = ''
        password = ''

        # NOTE: check for either http://xmpp.org/extensions/xep-0045.html#invite
        # or direct invites http://xmpp.org/extensions/xep-0249.html
        if xpath.matches('/message/x/invite', element):
            from_jid = jid.JID(element['from'])
            to_jid = jid.JID(element['to'])

            if from_jid.host == self.conference_host:
                channel = from_jid.userhost()
            else:
                channel = to_jid.userhost()

            # This is a hack around a unicode bug in twisted queryForString
            strings = xpath.queryForStringList('/message/x/password', element)
            if strings:
                password = strings[0]
        elif xpath.matches('/message/x[@xmlns="jabber:x:conference"]', element):
            # Direct invite
            x = xpath.queryForNodes('/message/x', element)[0]
            channel = x['jid']
            password = x.attributes.get('password', '')
        else:
            # Probably not an invite, but the overly greedy xpath matched it. Ignore.
            return

        self.join(channel, password=password)

    def on_subscribe(self, element):
        """
        Handler that responds to 'buddy requests' from other users. This will acknowledge
        the request by approving it.

        :param element: A <presence/> element, instance of `twisted.words.xish.domish.Element`
        """
        message = domish.Element(('jabber:client', 'presence'), attribs={
            'to': element['from'],
            'from': self.jid.full(),
            'type': 'subscribed',
        })
        self.stream.send(message)

    def on_user_joined(self, element):
        """
        Handler called when a user enters a public room. Responsible for sending
        the ``user_joined`` signal (see :ref:`plugins.signals`)

        :param element: A <presence/> element, instance of `twisted.words.xish.domish.Element`
        """
        # NOTE: HipChat might send duplicates here. If this is a problem, ignore
        # presence stanzas that match /presence/x[@xmlns="http://hipchat.com/protocol/muc#room
        # or maybe more generally /presence/x/name
        nick = self.parse_nick(element)
        channel = self.parse_channel(element)
        logger.debug('User %s joined channel %s', nick, channel)
        smokesignal.emit('user_joined', self, nick, channel)

    def on_user_left(self, element):
        """
        Handler called when a user leaves a public room. Responsible for sending
        the ``user_left`` signal (see :ref:`plugins.signals`)

        :param element: A <presence/> element, instance of `twisted.words.xish.domish.Element`
        """
        nick = self.parse_nick(element)
        channel = self.parse_channel(element)
        logger.debug('User %s left channel %s', nick, channel)
        smokesignal.emit('user_left', self, nick, channel)

    @encodings.from_unicode_args
    def join(self, channel, password=None):
        """
        Join a channel, optionally with a passphrase required to join. Channels can either
        be a full, valid JID or a simple channel name like '#bots', which will be expanded
        into something like `bots@conference.example.com` (see :meth:`~Client.format_channel`)

        :param channel: the name of the channel to join
        :param key: an optional passphrase used to join the given channel
        """
        channel = self.format_channel(channel)
        logger.info("Joining channel %s", channel)

        element = domish.Element(('jabber:client', 'presence'), attribs={
            'to': '{channel}/{nick}'.format(channel=channel, nick=self.nickname),
            'from': self.jid.full(),
        })

        muc = domish.Element(('http://jabber.org/protocol/muc', 'x'))

        # Don't include room history
        hist = domish.Element(('', 'history'), attribs={
            'maxchars': '0',
            'maxstanzas': '0',
        })
        muc.addChild(hist)

        if password:
            muc.addElement('password', content=password)

        element.addChild(muc)

        self.stream.send(element)
        self.joined(channel)

    @encodings.from_unicode_args
    def leave(self, channel, reason=None):
        """
        Leave a channel, optionally with a reason for leaving

        :param channel: the name of the channel to leave
        :param reason: an optional reason for leaving
        """
        logger.info("Leaving channel %s: %s", channel, reason)
        element = domish.Element(('jabber:client', 'presence'), attribs={
            'to': self.format_channel(channel),
            'from': self.jid.full(),
            'type': 'unavailable',
        })
        self.stream.send(element)
        self.left(channel)

    def format_channel(self, channel):
        """
        Formats a channel as a valid JID string. This will operate with a fallback
        of ``channel@conference_host`` should any of the following conditions happen:

        - Parsing the channel as a JID fails with `twisted.words.protocols.jabber.jid.InvalidFormat`
        - Either the ``user`` or ``host`` portion of the parsed JID is empty

        Any prefixed '#' characters are removed. For example, assuming a conference host
        of 'conf.example.com':

        - `#bots` would return `bots@conf.example.com`
        - `bots` would return `bots@conf.example.com`
        - `bots@rooms.example.com` would return `bots@rooms.example.com`
        - `bots@rooms.example.com/resource` would return `bots@rooms.example.com`

        :param channel: The channel to format as a full JID. Can be a simple string, '#' prefixed string,
                        or full room JID.
        :returns: The full user@host JID of the room
        """
        channel = channel.lstrip('#')
        fallback = '{channel}@{host}'.format(channel=channel,
                                             host=self.conference_host)

        try:
            channel_jid = jid.JID(channel)
        except jid.InvalidFormat:
            return fallback
        else:
            if not all((channel_jid.user, channel_jid.host)):
                logger.warning('Parsed channel jid %s is invalid', channel_jid.full())
                return fallback
            else:
                return channel_jid.userhost()
