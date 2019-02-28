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

import json
import re
import uuid

from functools import partial

import smokesignal
import requests

from twisted.internet import reactor, task
from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol

from helga import settings, log
from helga.comm.base import BaseClient
from helga.plugins import registry


logger = log.getLogger(__name__)

SLACK_API_BASE = 'https://slack.com/api/'


def api(action, **data):
    logger.debug('Slack API request: /%s -> %s', action, data)

    # Slack API key, eg xoxb-12345678901-A1b2C3deFgHiJkLmNoPqRsTu
    data.update({'token': settings.SERVER['API_KEY']})

    response = requests.post(SLACK_API_BASE + action, data=data)

    data = response.json()

    if not data['ok']:
        raise SlackError(api=action, error=data['error'])

    return data


class Factory(WebSocketClientFactory):
    """
    Handle a constructor with no args.
    Kill the reactor when the connection to the Slack RTM server drops.
    """
    def __init__(self):
        logger.info('Initiating Slack RTM start request')
        data = api('rtm.start', no_latest=1)

        # Make the protocol a partial so that we can send the full info from rtm.start
        self.protocol = partial(Client, data)

        logger.info('creating WebSocketClientFactory with %s', data['url'])

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
        # FIXME: need to handle auto reconnects
        logger.info('Connection to server lost: %s', reason)

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            delay = getattr(settings, 'AUTO_RECONNECT_DELAY', 5)
            reactor.callLater(delay, connector.connect)
        else:
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


class Client(WebSocketClientProtocol, BaseClient):

    def __init__(self, rtm_start_data, *a, **kw):
        BaseClient.__init__(self)

        # Slack prompts users to set up a bot account's name when setting up
        # the API key. So the bot's name is already defined server-side, and we
        # just have to look it up. In fact, we ignore settings.NICK.
        self.nickname = rtm_start_data['self']['name']

        # Additionally, it is just simpler to override the user's
        # COMMAND_PREFIX_BOTNICK setting here, so to reduce the need for manual
        # configuration.
        settings.COMMAND_PREFIX_BOTNICK = '@?' + self.nickname

        # Maps of channel/user id -> name
        channels = (
            (rtm_start_data.get('channels') or []) +
            (rtm_start_data.get('mpims') or []) +
            (rtm_start_data.get('ims') or []) +
            (rtm_start_data.get('groups') or [])
        )

        users = rtm_start_data.get('users') or []

        self._cache_all_channel_names(channels)
        self._cache_all_user_names(users)

        # FIXME: setup reactor recurring tasks to refresh the list of channels/users
        self.refresh_channels = task.LoopingCall(self._cache_all_channel_names)
        self.refresh_users = task.LoopingCall(self._cache_all_user_names)

        self.refresh_channels.start(60, now=False)
        self.refresh_users.start(60, now=False)

        # Check if i'm a bot
        self._i_am_bot = False

        for user in users:
            if user['name'] == self.nickname:
                self._i_am_bot = user['is_bot']
                break

        # With websockets, we'll get replies to messages we attempt to send.
        # Keep track of them in a map of request-id -> message
        self._requests = {}

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

        # Is this a response to a previous message?
        if 'reply_to' in data:
            return self.onMessageAck(int(data['reply_to']), data)

        if 'type' not in data:
            # Don't know how to handle this
            return

        # Actions we'll never handle and reduce log noise
        if data['type'] in ('desktop_notification', 'user_typing'):
            return

        method_name = 'slack_{}'.format(data['type'])

        if 'subtype' in data:
            method_name = '{}_{}'.format(method_name, data['subtype'])

        try:
            getattr(self, method_name)(data)
        except AttributeError:
            logger.info('No implementation for %r', method_name)
        except Exception:
            logger.exception('Failed to handle method call to %s', method_name)

    def onMessageAck(self, request_id, response):
        logger.debug('onMessageAck %s %s', request_id, response)

        # We're ACK'ing the request, so pop from the request map
        request = self._requests.pop(request_id, None)

        if not request:
            logger.error('Received response for unknown message ID %s: %s', request_id, response)
        elif not response['ok']:
            logger.error('WebSocket request %s received error %s', request_id, response.get('error', ''))

    def slack_hello(self, data):
        """
        Called when the client has successfully signed on to Slack. Sends the
        ``signon`` signal (see :ref:`plugins.signals`)

        :param data: dict from JSON received in WebSocket message
        """
        smokesignal.emit('signon', self)

    def slack_message_channel_join(self, data):
        user = self._get_user_name(data['user'])
        channel = self._get_channel_name(data['channel'])
        smokesignal.emit('user_joined', self, user, channel)

    def slack_message_channel_leave(self, data):
        user = self._get_user_name(data['user'])
        channel = self._get_channel_name(data['channel'])
        smokesignal.emit('user_left', self, user, channel)

    def slack_message(self, data):
        """
        Handler for an incoming Slack message event. This method allows the
        plugin manager to send the message to all registered plugins. Should
        the plugin manager yield a response, it will be sent back over Slack.

        :param data: dict from JSON received in WebSocket message
        """
        # Look up the human-readable name for this user ID.
        user = self._get_user_name(data['user'])

        # If we don't ignore this, we'll get infinite replies
        if user == self.nickname:
            return

        channel = self._get_channel_name(data['channel'])

        if channel:
            # If this was a legit channel, prefix it with a hash for later consistency
            channel = u'#{}'.format(channel)

        # I'm not sure if 100% of all messages have a "text" value. Use a blank
        # string fallback to be safe.
        message = data.get('text', '')

        message = self._parse_incoming_message(message)

        # Log the incoming message
        logger.debug('[<--] %s/%s - %s', channel, user, message)

        # Some things should go first
        try:
            channel, user, message = registry.preprocess(self, channel, user, message)
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
        logger.debug('[-->] %s - /me %s', channel, message)
        return self._send_message(channel, message, subtype='me_message')

    def msg(self, channel, message):
        """
        Send a message over Slack to the specified channel.

        :param channel: The Slack channel to send the message to (eg
                        "general").
        :type  channel: ``str`` or ``SlackChannel``
        :param message: The message to send (plain string, or JSON)
        :type  message: ``str``
        """
        # First, sanitize the message
        message = self._sanitize(message)

        logger.debug('[-->] %s - %s', channel, message)

        if channel.startswith('#'):
            return self._send_message(channel, message)
        else:
            # In this case we need to fiddle with the API, do this async
            maybe_channel = self._get_channel_id(self._get_user_id(channel))

            if maybe_channel:
                return self._send_message(maybe_channel, message)
            else:
                reactor.callLater(0, self._async_msg_user, channel, message)

        # TODO: support better/more complex response types using chat.postMessage

    def _async_msg_user(self, user, message):
        user_id = self._get_user_id(user)

        # Hit the Web API
        try:
            data = api('im.open', user=user_id)
        except SlackError:
            logger.exception('Cannot initiate private message with user %s', user_id)
            return

        channel_id = data['channel']['id']

        # Update our internal cache if we don't know about it
        if not data.get('already_open', False):
            channel_name = data['channel']['name']
            self._channel_names[channel_id] = channel_name

        self._send_message(self._get_channel_name(channel_id), message)

    def leave(self, channel, *args, **kwargs):
        channel = self._get_channel_id(channel)

        if self._i_am_bot:
            msg = 'Bots cannot leave channels by themselves. They must be kicked'
            logger.warning('Cannot leave %s: %s', channel, msg)
            return msg
        else:
            reactor.callLater(0, api, 'channels.leave', channel=channel)

    def join(self, channel, *args, **kwargs):
        if self._i_am_bot:
            msg = 'Bots cannot join channels by themselves. They must be invited'
            logger.warning('Cannot join %s: %s', channel, msg)
            return msg
        else:
            reactor.callLater(0, api, 'channels.join', name=channel)

    def _get_channel_name(self, channel_id):
        return self._channel_names.get(channel_id, '')

    def _get_channel_id(self, name):
        name = name.lstrip('#')

        for chan_id, chan_name in self._channel_names.iteritems():
            if chan_name == name:
                return chan_id

        return None

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
        return self._user_names.get(user_id, '')

    def _get_user_id(self, name):
        """
        Get the ID for a user, searching by name.

        :param name: user name, eg. "kdreyer"
        :type  name: ``str``

        :returns: user name, eg "U1234567890"
        :rtype: ``str``
        :raises: RuntimeError: If the requested user could not be found.
        """
        name = name.lstrip('@')

        for user_id, user_name in self._user_names.iteritems():
            if user_name == name:
                return user_id

        return None

    def _cache_all_channel_names(self, channels=None):
        """
        Hit the Web API and store all channel id/name pairs in
        self._channel_names.

        :raises: SlackError: If Web API request fails
        """
        if channels is None:
            logger.debug('Fetching full channel list from slack API')
            try:
                channels = api('channels.list')['channels']
                channels.extend(api('groups.list')['groups'])
                channels.extend(api('mpim.list')['groups'])
                channels.extend(api('im.list')['ims'])
            except SlackError:
                logger.exception('Failed to get full channel list from slack')
                return

        channel_names = {}

        for c in channels:
            try:
                channel_names[c['id']] = c['name']
            except KeyError:
                channel_names[c['id']] = c['user']

        self._channel_names = channel_names

    def _cache_all_user_names(self, users=None):
        """
        Hit the Web API and store all user id/name pairs in
        self._user_names.

        :raises: SlackError: If Web API request fails
        """
        if users is None:
            logger.debug('Fetching full user list from slack API')
            try:
                users = api('users.list')['members']
            except SlackError:
                logger.exception('Failed to get full user list from slack')
                return

        self._user_names = {}

        for user in users:
            self._user_names[user['id']] = user['name']

    def _parse_incoming_message(self, message):
        """
        Slack uses &, <, and > as control characters so that messages may
        contain special escaped sequences. Translate these to human-readable
        forms. In particular, we will translate "<@UUSERID>" or
        "<@UUSERID|foo>" to "@USER". Also look for similarly formatted channel
        names like "<#CHANNELID|channel-name>" and replace with "#channel-name".
        After these substitutions occur, any HTML-escaped occurrences of &, <, and >
        are unescaped back to their original forms, to allow plugins to receive
        the same message that was entered by the sender.

        :param message: message string to parse, eg "<@U0123ABCD> hello &lt;test&gt;".
        :returns: a translated string, eg. "@adeza hello <test>".
        """
        user_regex = r'(<@(U[0-9A-Z]+)(?:\|[^>]+)?>)'
        for full_match, user_id in re.findall(user_regex, message):
            user = self._get_user_name(user_id)
            message = message.replace(full_match, '@' + user)

        channel_regex = r'(<#([0-9A-Z]+)(?:\|[^>]+)?>)'
        for full_match, channel_id in re.findall(channel_regex, message):
            channel = self._get_channel_name(channel_id)
            message = message.replace(full_match, '#' + channel)
 
        # Unescape &, <, and > characters
        message = re.sub(r'&amp;', '&', message)
        message = re.sub(r'&lt;', '<', message)
        message = re.sub(r'&gt;', '>', message)
 
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

    def _send_message(self, channel, message, **extra):
        """
        Send a raw command ("message") over the WebSocket using autobahn's
        sendMessage().

        :param data: dict to send via WebSocket
        """
        if channel not in self._channel_names:
            channel = self._get_channel_id(channel)

        message_id = uuid.uuid4().int

        # Assemble JSON to send
        data = {
            'id': message_id,
            'channel': channel,
            'text': message,
            'type': 'message',
        }

        # Add any extra params
        data.update(extra)

        # Track and send
        self._requests[message_id] = data
        self.sendMessage(json.dumps(data))

    def slack_channel_joined(self, data):
        """
        Called when the bot joins a channel. Emits the "joined" smokesignal.

        :param data: dict from JSON received in WebSocket message
        """
        channel = data['channel']['name']

        logger.info('Joined %s', channel)

        # Update caches
        self.channels.add(channel)
        self._channel_names[data['channel']['id']] = channel

        smokesignal.emit('join', self, channel)

    def slack_channel_left(self, data):
        """
        Called when the bot leaves a channel. Emits the "left" smokesignal.

        :param data: dict from JSON received in WebSocket message
        """
        # Convert the slack channel id
        channel = self._get_channel_name(data['channel'])

        logger.info('Left %s', channel)

        # Update caches
        self.channels.discard(channel)
        self._channel_names.pop(data['channel'], None)

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

    # groups work like channel join/leave
    slack_group_joined = slack_channel_joined
    slack_group_left = slack_channel_left
    slack_group_rename = slack_channel_rename

    def slack_channel_deleted(self, data):
        """
        Triggers when a channel is deleted.
        """
        try:
            del self._channel_names[data['channel']['id']]
        except KeyError:
            pass


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
