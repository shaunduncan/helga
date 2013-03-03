# -*- coding: utf8 -*-
import re

from mock import patch
from unittest import TestCase

from helga.client import Message, HelgaClient


class MessageTestCase(TestCase):

    def setUp(self):
        self.message = Message('foo', '#bar', 'baz', True)

    def test_format_response_does_formatting(self):
        expected = 'foo #bar bar'
        self.message.response = '%(nick)s %(channel)s %(norm_channel)s'

        assert self.message.format_response() == expected

    def test_format_response_multiline_response(self):
        expected = 'foo\nbar\nbaz'
        self.message.response = ['foo', 'bar', 'baz']

        assert self.message.format_response() == expected

    def test_format_response_accepts_kwargs(self):
        expected = 'foo bar'
        self.message.response = 'foo %(kwarg)s'

        assert self.message.format_response(kwarg='bar') == expected


class HelgaClientTestCase(TestCase):

    def setUp(self):
        self.client = HelgaClient()

    def test_parse_nick(self):
        nick = self.client.parse_nick('foo!~foobar@localhost')
        assert nick == 'foo'

    @patch('helga.client.irc.IRCClient')
    def test_msg_encodes_utf_8(self, irc):
        uni_str = u'ಠ_ಠ'
        utf8_str = '\xe0\xb2\xa0_\xe0\xb2\xa0'

        self.client.msg('#foo', uni_str)
        irc.msg.assertCalledWith('#foo', utf8_str)

    def test_alterCollidedNick(self):
        self.client.alterCollidedNick('foo')
        assert re.match(r'foo_[\d]+', self.client.nickname)

    @patch('helga.client.helga')
    def test_userJoined_updates_nick(self, bot):
        self.client.userJoined('foo', '#bots')
        bot.update_user_nick.calledWith('foo', 'foo')

    @patch('helga.client.settings')
    @patch('helga.client.helga')
    def test_signedOn_sends_signal(self, bot, settings):
        settings.CHANNELS = []

        self.client.signedOn()
        bot.on.assertCalledWith('signon')

    @patch('helga.client.helga')
    @patch('helga.client.irc.IRCClient')
    def test_connectionMade_sets_bot_client(self, irc, bot):
        self.client.connectionMade()
        assert bot.client == self.client

    @patch('helga.client.helga')
    @patch('helga.client.irc.IRCClient')
    def test_connectionLost_unsets_bot_client(self, irc, bot):
        bot.client = self.client
        self.client.connectionLost('something catastrophic')
        assert bot.client is None

    @patch('helga.client.helga')
    def test_privmsg(self, bot):
        input = '  this is the input  '
        channel = '#bots'
        user = 'foo!~bar@baz'

        self.client.privmsg(user, channel, input)
        msg = bot.process.call_args[0][0]

        # Test what it does
        assert isinstance(msg, Message)
        assert msg.message == 'this is the input'
