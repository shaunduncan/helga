# -*- coding: utf8 -*-
import re

from mock import Mock, patch
from unittest import TestCase

from helga import comm


class ClientTestCase(TestCase):

    def setUp(self):
        self.client = comm.Client()

    def test_parse_nick(self):
        nick = self.client.parse_nick('foo!~foobar@localhost')
        assert nick == 'foo'

    @patch('helga.comm.irc.IRCClient')
    def test_me_converts_from_unicode(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'
        self.client.me('#foo', snowman)
        irc.describe.assert_called_with('#foo', bytes)

    @patch('helga.comm.irc.IRCClient')
    def test_msg_sends_byte_string(self, irc):
        snowman = u'☃'
        bytes = '\xe2\x98\x83'

        self.client.msg('#foo', snowman)
        irc.msg.assert_called_with('#foo', bytes)

    def test_alterCollidedNick(self):
        self.client.alterCollidedNick('foo')
        assert re.match(r'foo_[\d]+', self.client.nickname)

    @patch('helga.comm.settings')
    @patch('helga.comm.smokesignal')
    def test_signedOn_sends_signal(self, signal, settings):
        settings.CHANNELS = []
        self.client.signedOn()
        signal.emit.assert_called_with('signon')

    @patch('helga.comm.registry')
    def test_privmsg_sends_single_string(self, registry):
        self.client.msg = Mock()
        registry.process.return_value = ['line1', 'line2']

        self.client.privmsg('foo!~bar@baz', '#bots', 'this is the input')

        args = self.client.msg.call_args[0]
        assert args[0] == '#bots'
        assert args[1] == 'line1\nline2'

    @patch('helga.comm.registry')
    def test_privmsg_responds_to_user_when_private(self, registry):
        self.client.nickname = 'helga'
        self.client.msg = Mock()
        registry.process.return_value = ['line1', 'line2']

        self.client.privmsg('foo!~bar@baz', 'helga', 'this is the input')

        assert self.client.msg.call_args[0][0] == 'foo'
