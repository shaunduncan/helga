# -*- coding: utf8 -*-
import re

from mock import Mock, call, patch
from unittest import TestCase

from helga.comm import irc


class FactoryTestCase(TestCase):

    def setUp(self):
        self.factory = irc.Factory()

    def test_build_protocol(self):
        client = self.factory.buildProtocol('address')
        assert client.factory == self.factory

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.reactor')
    def test_client_connection_lost_retries(self, reactor, settings):
        settings.AUTO_RECONNECT = True
        settings.AUTO_RECONNECT_DELAY = 1
        connector = Mock()
        self.factory.clientConnectionLost(connector, Exception)
        reactor.callLater.assert_called_with(1, connector.connect)

    @patch('helga.comm.irc.settings')
    def test_client_connection_lost_raises(self, settings):
        settings.AUTO_RECONNECT = False
        connector = Mock()
        self.assertRaises(Exception, self.factory.clientConnectionLost, connector, Exception)

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.reactor')
    def test_client_connection_failed(self, reactor, settings):
        settings.AUTO_RECONNECT = False
        self.factory.clientConnectionFailed(Mock(), reactor)
        assert reactor.stop.called

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.reactor')
    def test_client_connection_failed_retries(self, reactor, settings):
        settings.AUTO_RECONNECT = True
        settings.AUTO_RECONNECT_DELAY = 1
        connector = Mock()
        self.factory.clientConnectionFailed(connector, reactor)
        reactor.callLater.assert_called_with(1, connector.connect)


class ClientTestCase(TestCase):

    def setUp(self):
        self.client = irc.Client()

    def test_parse_nick(self):
        nick = self.client.parse_nick('foo!~foobar@localhost')
        assert nick == 'foo'

    def test_parse_nick_unicode(self):
        nick = self.client.parse_nick(u'☃!~foobar@localhost')
        assert nick == u'☃'

    @patch('helga.comm.irc.irc.IRCClient')
    def test_me_converts_from_unicode(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'
        self.client.me('#foo', snowman)
        irc.describe.assert_called_with(self.client, '#foo', bytes)

    @patch('helga.comm.irc.irc.IRCClient')
    def test_msg_sends_byte_string(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'

        self.client.msg('#foo', snowman)
        irc.msg.assert_called_with(self.client, '#foo', bytes)

    def test_alterCollidedNick(self):
        self.client.alterCollidedNick('foo')
        assert re.match(r'^foo_[\d]+$', self.client.nickname)

        # Should take the first part up to '_'
        self.client.alterCollidedNick('foo_bar')
        assert re.match(r'^foo_[\d]+$', self.client.nickname)

    def test_erroneousNickFallback(self):
        assert re.match(r'^helga_[\d]+$', self.client.erroneousNickFallback)

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.smokesignal')
    def test_signedOn(self, signal, settings):
        snowman = u'☃'

        settings.CHANNELS = [
            ('#bots',),
            ('#foo', 'bar'),
            (u'#baz', snowman),  # Handles unicode gracefully?
            ['#a', 'b'],  # As a list
            '#test',  # Single channel
        ]

        with patch.object(self.client, 'join') as join:
            self.client.signedOn()
            assert join.call_args_list == [
                call('#bots'),
                call('#foo', 'bar'),
                call('#baz', snowman),
                call('#a', 'b'),
                call('#test'),
            ]

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.smokesignal')
    def test_signedOn_sends_signal(self, signal, settings):
        settings.CHANNELS = []
        self.client.signedOn()
        signal.emit.assert_called_with('signon', self.client)

    @patch('helga.comm.irc.registry')
    def test_privmsg_sends_single_string(self, registry):
        self.client.msg = Mock()
        registry.process.return_value = ['line1', 'line2']

        self.client.privmsg('foo!~bar@baz', '#bots', 'this is the input')

        args = self.client.msg.call_args[0]
        assert args[0] == '#bots'
        assert args[1] == 'line1\nline2'

    @patch('helga.comm.irc.registry')
    def test_privmsg_responds_to_user_when_private(self, registry):
        self.client.nickname = 'helga'
        self.client.msg = Mock()
        registry.process.return_value = ['line1', 'line2']

        self.client.privmsg('foo!~bar@baz', 'helga', 'this is the input')

        assert self.client.msg.call_args[0][0] == 'foo'

    @patch('helga.comm.irc.registry')
    def test_action(self, registry):
        self.client.msg = Mock()
        registry.process.return_value = ['eats the snack']

        self.client.action('foo!~bar@baz', '#bots', 'offers helga a snack')

        args = self.client.msg.call_args[0]
        assert args[0] == '#bots'
        assert args[1] == 'eats the snack'


    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.irc.IRCClient')
    def test_connectionMade(self, irc, settings):
        self.client.connectionMade()
        irc.connectionMade.assert_called_with(self.client)

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.irc.IRCClient')
    def test_connectionLost(self, irc, settings):
        self.client.connectionLost('an error...')
        irc.connectionLost.assert_called_with(self.client, 'an error...')

    @patch('helga.comm.irc.settings')
    @patch('helga.comm.irc.irc.IRCClient')
    def test_connectionLost_handles_unicode(self, irc, settings):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'
        self.client.connectionLost(snowman)
        irc.connectionLost.assert_called_with(self.client, bytes)

    @patch('helga.comm.irc.smokesignal')
    def test_joined(self, signal):
        # Test str and unicode
        for channel in ('foo', u'☃'):
            assert channel not in self.client.channels
            self.client.joined(channel)
            assert channel in self.client.channels
            signal.emit.assert_called_with('join', self.client, channel)

    @patch('helga.comm.irc.smokesignal')
    def test_left(self, signal):
        # Test str and unicode
        for channel in ('foo', u'☃'):
            self.client.channels.add(channel)
            self.client.left(channel)
            assert channel not in self.client.channels
            signal.emit.assert_called_with('left', self.client, channel)

    def test_kickedFrom(self):
        # Test str and unicode
        for channel in ('foo', u'☃'):
            self.client.channels.add(channel)
            self.client.kickedFrom(channel, 'me', 'no bots allowed')
            assert channel not in self.client.channels

    def test_on_invite(self):
        with patch.object(self.client, 'join') as join:
            self.client.nickname = 'helga'
            self.client.on_invite('me', 'helga', '#bots')
            assert join.called

    def test_on_invite_ignores_other_invites(self):
        with patch.object(self.client, 'join') as join:
            self.client.nickname = 'helga'
            self.client.on_invite('me', 'someone_else', '#bots')
            assert not join.called

    def test_irc_unknown(self):
        with patch.object(self.client, 'on_invite') as on_invite:
            self.client.irc_unknown('me', 'INVITE', ['helga', '#bots'])
            on_invite.assert_called_with('me', 'helga', '#bots')

            on_invite.reset_mock()
            self.client.irc_unknown('me', 'SOME_COMMAND', [])
            assert not on_invite.called

    @patch('helga.comm.irc.smokesignal')
    def test_userJoined(self, signal):
        user = 'helga!helgabot@127.0.0.1'
        self.client.userJoined(user, '#bots')
        signal.emit.assert_called_with('user_joined', self.client, 'helga', '#bots')

    @patch('helga.comm.irc.smokesignal')
    def test_userLeft(self, signal):
        user = 'helga!helgabot@127.0.0.1'
        self.client.userLeft(user, '#bots')
        signal.emit.assert_called_with('user_left', self.client, 'helga', '#bots')

    @patch('helga.comm.irc.irc.IRCClient')
    def test_join_converts_from_unicode(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'
        self.client.join(snowman, snowman)
        irc.join.assert_called_with(self.client, bytes, key=bytes)

    @patch('helga.comm.irc.irc.IRCClient')
    def test_leave_converts_from_unicode(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'
        self.client.leave(snowman, snowman)
        irc.leave.assert_called_with(self.client, bytes, reason=bytes)

    @patch('helga.comm.irc.log')
    def test_get_channel_logger_no_existing_logger(self, log):
        self.client.channel_loggers = {}
        log.get_channel_logger.return_value = 'foo'

        assert 'foo' == self.client.get_channel_logger('#foo')
        assert '#foo' in self.client.channel_loggers

    @patch('helga.comm.irc.log')
    def test_get_channel_logger_existing_logger(self, log):
        self.client.channel_loggers = {'#foo': 'bar'}
        log.get_channel_logger.return_value = 'foo'

        assert 'bar' == self.client.get_channel_logger('#foo')
        assert not log.get_channel_logger.called

    @patch('helga.comm.irc.settings')
    def test_log_channel_message(self, settings):
        settings.CHANNEL_LOGGING = True
        logger = Mock()

        with patch.object(self.client, 'get_channel_logger'):
            self.client.get_channel_logger.return_value = logger
            self.client.log_channel_message('foo', 'bar', 'baz')
            self.client.get_channel_logger.assert_called_with('foo')
            logger.info.assert_called_with('baz', extra={'nick': 'bar'})
