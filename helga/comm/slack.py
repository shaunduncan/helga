"""
Twisted protocol and communication implementations for Slack.com
"""

# TODO:
# - Bug: Make auto-restart work.
# - Bug: Make channel logging work.
# - Cleanup: Abstract Web API calls (see
#   https://github.com/slackhq/python-slackclient for inspiration, in
#   particular its api_call() method)
# - Feature: Replace Python's requests with treq so we don't block the
#   Twisted reactor (maybe even create a "txslackclient" library in the distant
#   future?)

from collections import defaultdict
import json
import re

import smokesignal
import requests

from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol
from sys import maxint

from helga import settings, log
from helga.plugins import registry


logger = log.getLogger(__name__)


class Factory(WebSocketClientFactory):
    """
    Handle a constructor with no args.
    Kill the reactor when the connection to the Slack RTM server drops.
    """
    def __init__(self):
        # Slack API key, eg xoxb-12345678901-A1b2C3deFgHiJkLmNoPqRsTu
        self.api_key = settings.SERVER['API_KEY']

        logger.info('Initiating Slack RTM start request')
        API_URL = 'https://slack.com/api/rtm.start'
        response = requests.post(API_URL, data={'token': self.api_key})
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='rtm.start', error=data['error'])

        self.protocol = Client

        logger.info('creating WebSocketClientFactory with %s' % data['url'])
        return WebSocketClientFactory.__init__(self, url=data['url'])

    def clientConnectionLost(self, connector, reason):
        """
        Handler for when the Slack RTM connection is lost.
        TODO: Instead of stopping the reactor, we should handle auto reconnect
        if helga is configured for it (see settings
        :data:`~helga.settings.AUTO_RECONNECT` and
        :data:`~helga.settings.AUTO_RECONNECT_DELAY`)
        NOTE: this approach needs more work, because it seems to fire even when
        the main helga process receives SIGINT (ctrl-c).
        """
        logger.info('Connection to server lost: %s', reason)
        reactor.stop()
        raise reason

    def clientConnectionFailed(self, connector, reason):
        """
        Handler for when the Slack RTM connection fails.
        TODO: Instead of stopping the reactor, we should handle auto reconnect
        if helga is configured for it (see settings
        :data:`~helga.settings.AUTO_RECONNECT` and
        :data:`~helga.settings.AUTO_RECONNECT_DELAY`)
        """
        logger.warning('Connection to server failed: %s', reason)
        reactor.stop()


class Client(WebSocketClientProtocol):

    def __init__(self, *a, **kw):
        # Slack API key, eg xoxb-12345678901-A1b2C3deFgHiJkLmNoPqRsTu
        self.api_key = settings.SERVER['API_KEY']

        # Slack prompts users to set up a bot account's name when setting up
        # the API key. So the bot's name is already defined server-side, and we
        # just have to look it up. In fact, we ignore settings.NICK.
        self.nickname = self._get_self_name()

        # Additionally, it is just simpler to override the user's
        # COMMAND_PREFIX_BOTNICK setting here, so to reduce the need for manual
        # configuration.
        settings.COMMAND_PREFIX_BOTNICK = '@?' + self.nickname

        # logger.debug('My user name in Slack is "%s".' % self.nickname)

        self.last_message = defaultdict(dict)   # Dict of x[channel][nick]
        self._channel_names = {} # Map channel IDs to names
        self._user_names = {}    # Map user IDs to names
        return WebSocketClientProtocol.__init__(self, *a, **kw)

    def onMessage(self, msg, binary):
        """
        Receive a raw message from the Slack WebSocket.
        The message is a JSON string. Decode it, and if there is a "type" key,
        use that value to call a similarly-named "slack_" function, if one
        exists. For example, if the message string was '{"type":"hello"}', then
        we will call the self.slack_hello() function, if it exists.
        """
        try:
            data = json.loads(msg)
        except ValueError as e:
            logger.error('Error parsing WebSocket message %s : %s' % (msg, e))
            return
        if data.get('type', None) is not None:
            method_name = 'slack_' + data['type']
            method = getattr(self, method_name, False)
            if hasattr(method, '__call__'):
                method(data)

    def slack_hello(self, data):
        """
        Called when the client has successfully signed on to Slack. Sends the
        ``signon`` signal (see :ref:`plugins.signals`)

        :param data: dict from JSON received in WebSocket message
        """
        self._next_message_id = 1
        # Might as well cache all channel and user names to save individual
        # lookups later.
        self._cache_all_channel_names()
        self._cache_all_user_names()
        smokesignal.emit('signon', self)

    def slack_message(self, data):
        """
        Handler for an incoming Slack message event. This method allows the
        plugin manager to send the message to all registered plugins. Should
        the plugin manager yield a response, it will be sent back over Slack.

        :param data: dict from JSON received in WebSocket message
        """
        # If this was a "message_changed" edit, process that message instead.
        # TODO: we probably want to avoid the cases where Slack itself edits a
        # message, eg when unfurling a link or media?
        if data.get('subtype', None) == 'message_changed':
            data['message']['channel'] = data['channel']
            data = data['message']

        # Look up the human-readable name for this user ID.
        user = self._get_user_name(data['user'])

        # Get a SlackChannel object for this channel ID.
        channel = self._get_slack_channel(id_=data['channel'])

        # I'm not sure if 100% of all messages have a "text" value. Use a blank
        # string fallback to be safe.
        message = data.get('text', '')

        message = self._parse_incoming_message(message)

        # Log the incoming message
        logger.debug('[<--] %s/%s - %s', channel, user, message)

        # Emit "user_joined" or "user_left" smokesignals
        if data.get('subtype', None) == 'channel_join':
            logger.info('smokesignal user_joined(%s, %s)', user, channel)
            smokesignal.emit('user_joined', self, user, channel)
        if data.get('subtype', None) == 'channel_leave':
            logger.info('smokesignal user_left(%s, %s)', user, channel)
            smokesignal.emit('user_left', self, user, channel)

        # If we don't ignore this, we'll get infinite replies
        if user == self.nickname:
            return

        # Some things should go first
        try:
            channel, user, message = registry.preprocess(self, channel,
                                                         user, message)
        except (TypeError, ValueError):
            pass

        # Update last message
        self.last_message[channel][user] = message

        responses = registry.process(self, channel, user, message)

        if responses:
            return self.msg(channel, u'\n'.join(responses))

    def me(self, channel, message):
        """
        Send a "/me" message over Slack to the specified channel.

        Note that this must be a plaintext message (no attachments).

        :param channel: The Slack channel to send the message to (eg
                        "general").
        :type  channel: ``str``
        :param message: The message to send (string)
        :type  message: ``str``
        """
        # Slack does not support "/me" commands via the API, so we do the next
        # best thing: prepend our nickname to the message.
        return self.msg(channel, '@%s %s' % (self.nickname, message))

    def msg(self, channel, message):
        """
        Send a message over Slack to the specified channel.

        If the message is a JSON string, this function will parse it into a
        dict and use the Slack Web API to send the message data, so you can
        specify attachments and formatting. The JSON must be a dict that
        contains a key named "text". For example, {"text": "this is my
        message"}. Optionally, you can specify an "attachments" key as well,
        and the value for "attachments" should follow the Slack API
        documentation.

        If the message is not a valid JSON string, this function will assume it
        is simply a plaintext message, and will use the Slack WebSocket
        connection to send it (which only supports plaintext messages, no
        attachments or formatting)

        :param channel: The Slack channel to send the message to (eg
                        "general").
        :type  channel: ``str`` or ``SlackChannel``
        :param message: The message to send (plain string, or JSON)
        :type  message: ``str``
        """
        try:
            # SlackChannel object?
            channel_id = channel.id_
        except AttributeError:
            if str(channel).startswith('#'):
                # It's a human-readable channel name, like "#general".
                channel = self._get_slack_channel(name=channel[1:])
            else:
                # It's a individual's username.
                channel = self._get_slack_im(channel)
        message = self._sanitize(message)
        try:
            message_data = json.loads(message)
        except ValueError:
            # The plugin response was not valid JSON. Assume it's just a
            # plaintext message string.
            logger.debug('[-->] %s - %s', channel, message)
            return self._send_command({
                'type': 'message',
                'channel': channel.id_,
                'text': message,
            })

        attachments = message_data.get('attachments', None)

        # TODO: log the "fallback" text for every attachment, rather than the
        # too-general "+attachments" string here.
        logger.debug('[-->] %s - %s (+attachments)', channel, text)

        API_URL = 'https://slack.com/api/chat.postMessage'
        response = requests.post(API_URL, data={
                                                'token': self.api_key,
                                                'channel': channel.id_,
                                                'text': text,
                                                'as_user': True,
                                                'attachments': attachments,
                                               })
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='chat.postMessage', error=data['error'])

    def _get_slack_channel(self, id_=None, name=None):
        """
        Get a SlackChannel object by name or ID.

        :param id_: channel ID, for example "C123456" (or "D123456" or
                    "G123456").
        :type  id_: ``str``

        :param name: channel name, for example "general"
        :type  name: ``str``

        :rtype: ``SlackChannel``
        :raises: SlackError: If Web API request fails, for example if the
                             channel could not be found.
        """
        if id_ is None and name is None:
            raise ValueError('must specify an id_ or name parameter')
        if id_ is not None and name is not None:
            raise ValueError('specify only an id_ or a name parameter')
        if id_ is not None:
            return self._get_slack_channel_by_id(id_)
        else:
            return self._get_slack_channel_by_name(name)

    def _get_slack_channel_by_id(self, id_):
        """
        Get a SlackChannel object by a channel ID.

        :param id_: channel ID, for example "C123456" (or "D123456" or
                    "G123456")
        :type  id_: ``str``

        :rtype: ``SlackChannel``
        :raises: SlackError: If Web API request fails, for example if the
                             channel could not be found.
        """
        channel = SlackChannel(id_=id_)
        if id_.startswith('D') or id_.startswith('G'):
            # No friendly name, just return our object with id_.
            channel.name = id_
            return channel
        # Assume we have a "C" channel with a name to look up.
        try: # check cache first
            channel.name = self._channel_names[id_]
            return channel
        except KeyError:
            pass
        # Hit the Web API
        API_URL = 'https://slack.com/api/channels.info'
        response = requests.post(API_URL, data={
                                                'token': self.api_key,
                                                'channel': id_,
                                               })
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='channels.info', error=data['error'])
        # Cache this name and return it
        channel.name = data['channel']['name']
        self._channel_names[channel_id] = channel.name
        return channel

    def _get_slack_channel_by_name(self, name):
        """
        Get a SlackChannel object by a channel name.

        :param name: channel name, for example "general"
        :type  name: ``str``

        :rtype: ``SlackChannel``
        :raises: RuntimeError: If the requested channel could not be found.
        """
        # check if we need to refresh the cache
        if name not in self._channel_names.values():
            self._cache_all_channel_names()

        for c_id, c_name in self._channel_names.iteritems():
            if c_name == name:
                return SlackChannel(id_=c_id, name=c_name)
        raise RuntimeError('Could not find channel ID for "%s"', name)

    def _cache_all_channel_names(self):
        """
        Hit the Web API and store all channel id/name pairs in
        self._channel_names.

        :raises: SlackError: If Web API request fails
        """
        API_URL = 'https://slack.com/api/channels.list'
        response = requests.post(API_URL, data={'token': self.api_key})
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='channels.list', error=data['error'])
        self._channel_names = {}
        for c in data['channels']:
            self._channel_names[c['id']] = c['name']

    def _cache_all_user_names(self):
        """
        Hit the Web API and store all user id/name pairs in
        self._user_names.

        :raises: SlackError: If Web API request fails
        """
        API_URL = 'https://slack.com/api/users.list'
        response = requests.post(API_URL, data={'token': self.api_key})
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='users.list', error=data['error'])
        self._user_names = {}
        for user in data['members']:
            self._user_names[user['id']] = user['name']

    def _get_slack_im(self, user):
        """
        Get a SlackChannel object by a user's name.

        :param user: username, for example "kdreyer".
        :type  user: ``str``

        :rtype: ``SlackChannel``
        :raises: SlackError: If Web API request fails, for example if the
                             user could not be found.
        """
        user_id = self._get_user_id(user)
        # Hit the Web API
        API_URL = 'https://slack.com/api/im.open'
        response = requests.post(API_URL, data={
                                                'token': self.api_key,
                                                'user': user_id,
                                               })
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='im.open', error=data['error'])
        return SlackChannel(id_=data['channel']['id'])

    def _get_user_name(self, user_id):
        """
        Get the username for a user ID.

        :param user_id: user ID, eg "U1234567890"
        :type  user_id: ``str``

        :returns: user name, eg "kdreyer"
        :rtype: ``str``
        :raises: SlackError: If Web API request fails, for example if the
                             user could not be found.
        """
        try: # check cache first
            return self._user_names[user_id]
        except KeyError:
            pass
        # Hit the Web API
        API_URL = 'https://slack.com/api/users.info'
        response = requests.post(API_URL, data={
                                                'token': self.api_key,
                                                'user': user_id,
                                               })
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='users.info', error=data['error'])
        # Cache this name and return it
        self._user_names[user_id] = data['user']['name']
        return self._user_names[user_id]

    def _get_user_id(self, name):
        """
        Get the ID for a user, searching by name.

        :param name: user name, eg. "kdreyer"
        :type  name: ``str``

        :returns: user name, eg "U1234567890"
        :rtype: ``str``
        :raises: RuntimeError: If the requested user could not be found.
        """
        # check if we need to refresh the cache
        if name not in self._user_names.values():
            self._cache_all_user_names()

        for u_id, u_name in self._user_names.iteritems():
            if u_name == name:
                return u_id
        raise RuntimeError('Could not find user ID for "%s"', name)

    def _get_self_name(self):
        """
        Get our own name.
        """
        API_URL = 'https://slack.com/api/auth.test'
        response = requests.post(API_URL, data={'token': self.api_key})
        data = response.json()
        if data['ok'] is not True:
            raise SlackError(api='auth.test', error=data['error'])
        return data['user']

    def _parse_incoming_message(self, message):
        """
        Slack uses &, <, and > as control characters so that messages may
        contain special escaped sequences. Translate these to human-readable
        forms. In particular, we will translate "<@UUSERID>" or
        "<@UUSERID|foo>" to "@USER".

        :param message: message string to parse, eg "<@U0123ABCD> hello".
        :returns: a translated string, eg. "@adeza hello".
        """
        user_regex = r'<@(U[0-9A-Z]+)(?:\|[^>]+)?>'
        for user_id in re.findall(user_regex, message):
            user = self._get_user_name(user_id)
            message = re.sub(user_regex, '@' + user, message)
        return message

    def _sanitize(self, message):
        """
        Sanitize an outgoing message for submission to Slack's API. Note that
        the Slack API requires that we purposefully only escape these three
        characters, not all HTML entities.

        :param message: message string to sanitize, eg "look over there ->"
        """
        message = re.sub(r'&', '&amp;', message)
        message = re.sub(r'<', '&lt;', message)
        message = re.sub(r'>', '&gt;', message)
        return message

    def _send_command(self, data):
        """
        Send a raw command ("message") over the WebSocket using autobahn's
        sendMessage().

        :param data: dict to send via WebSocket
        """
        # Assemble JSON to send
        msg = data
        msg['id'] = self._next_message_id
        self.sendMessage(json.dumps(msg))
        self._next_message_id += 1
        if self._next_message_id >= maxint:
            self._next_message_id = 1

    def slack_presence_change(self, data):
        """
        Called when a user signs in or out (or becomes "active" or "away").
        Currently a no-op.

        :param data: dict from JSON received in WebSocket message
        """
        # Some things we could do:
        # user = self._get_user_name(data['user'])
        # logger.info('presence_change: %s' % data)
        pass

    def slack_channel_joined(self, data):
        """
        Called when the bot joins a channel. Emits the "joined" smokesignal.

        :param data: dict from JSON received in WebSocket message
        """
        logger.debug('channel_joined: %s' % data)
        channel = data['channel']['name']
        smokesignal.emit('joined', self, channel)

    def slack_channel_left(self, data):
        """
        Called when the bot leaves a channel. Emits the "left" smokesignal.

        :param data: dict from JSON received in WebSocket message
        """
        logger.info('channel_left: %s' % data)
        # It seems that Slack's channel.info web API won't give us the channel
        # name at this point (since we've already left?) so we have to catch
        # the error and pass the raw channel ID :(
        try:
            channel = self._get_channel_name(data['channel'])
        except SlackError, e:
            logger.warning(e.message)
            if e.error == 'channel_not_found':
                # No name was available, so just use the raw channel ID
                channel = data['channel']
            else:
                raise
        logger.info('left channel %s' % channel)
        smokesignal.emit('left', self, channel)

    def slack_channel_created(self, data):
        """
        Triggers when a new channel is created.
        """
        id_ = data['channel']['id']
        name = data['channel']['name']
        self._channel_names[id_] = name

    # channel_rename is the exact same logic as channel_create
    slack_channel_rename = slack_channel_created

    def slack_channel_deleted(self, data):
        """
        Triggers when a channel is deleted.
        """
        try:
            del self._channel_names[data['channel']['id']]
        except KeyError:
            pass


class SlackChannel(object):
    """
    Internal representation of a Slack channel, with an "id" (``id_``) and
    human-readable name.
    """
    def __init__(self, id_, name=None):
        """
        :param id_: The channel ID, eg "C1234", "D1234", "G1234".
        :param name: The human-readable channel name
        """
        if id_ is not None and id_[0] not in ('C', 'D', 'G'):
            msg = 'Invalid Slack channel ID: %s (must start with C, D, or G)'
            raise RuntimeError(msg % _id)
        self.id_ = id_
        self.name = name

    def __str__(self):
        return str(self.name)

class SlackError(RuntimeError):
    """
    Raise this when the Slack Web API returns an error.
    """
    def __init__(self, api, error, *args):
        """
        :param api: The API URL endpoint, for example "channels.info"
        :param error: "error" key from JSON response, for example
                      "channel_not_found"
        """
        self.api = api
        self.error = error
        message = '%s in %s' % (error, api)
        self.message = message
        super(SlackError, self).__init__(message, *args)
