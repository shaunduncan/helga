from mock import Mock
from unittest import TestCase

from helga.extensions.base import (CommandExtension,
                                   ContextualExtension)
from helga.tests.util import mock_bot


class ContextualExtensionTestCase(TestCase):

    def setUp(self):
        self.ext = ContextualExtension(mock_bot())

    def test_contextualize_not_found(self):
        self.ext.context = r'foo'
        msg = Mock(message='bar', response=None)
        self.ext.contextualize(msg)
        assert not msg.response

    def test_contextualize_returns_many(self):
        self.ext.allow_many = True
        self.ext.context = r'foo[\d]+'
        self.ext.response_fmt = '%(response)s'
        msg = Mock(message='two things: foo1 and foo2')

        self.ext.contextualize(msg)
        assert msg.response == 'foo1 foo2'

    def test_contextualize_returns_one(self):
        self.ext.allow_many = False
        self.ext.context = r'foo[\d]+'
        self.ext.response_fmt = '%(response)s'
        msg = Mock(message='two things: foo1 and foo2')

        self.ext.contextualize(msg)
        assert msg.response == 'foo1'

    def test_contextualize_no_duplicates(self):
        self.ext.allow_many = True
        self.ext.context = r'foo[\d]+'
        self.ext.response_fmt = '%(response)s'
        msg = Mock(message='foo1 foo1 foo1')

        self.ext.contextualize(msg)
        assert msg.response == 'foo1'


class CommandExtensionTestCase(TestCase):

    def setUp(self):
        self.ext = CommandExtension(mock_bot())

    def test_parse_command(self):
        self.ext.usage = '[FOO] [BAR] [BAZ]'
        msg = Mock(message='foo bar baz')

        opts = self.ext.parse_command(msg)
        assert opts['FOO'] == 'foo'
        assert opts['BAR'] == 'bar'
        assert opts['BAZ'] == 'baz'

    def test_parse_command_no_match(self):
        self.ext.usage = 'foo [BAR]'
        msg = Mock(message='helga dosomething')
        assert self.ext.parse_command(msg) is None

    def test_parse_command_no_nick_required_arg(self):
        self.ext.usage = '[BOTNICK] foo'
        msg = Mock(message='foo')
        assert self.ext.parse_command(msg)

    def test_should_handle_message_private_without_nick(self):
        msg = Mock(is_public=False)
        opts = {
            'foo': True
        }

        assert self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_private_with_nick(self):
        msg = Mock(is_public=False)
        opts = {
            'BOTNICK': self.ext.bot.nick,
            'foo': True
        }

        assert self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_private_different_nick(self):
        msg = Mock(is_public=False)
        opts = {
            'BOTNICK': '@' + self.ext.bot.nick,
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_public_without_nick(self):
        msg = Mock(is_public=True)
        opts = {
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_public_with_nick(self):
        msg = Mock(is_public=True)
        opts = {
            'BOTNICK': self.ext.bot.nick,
            'foo': True
        }

        assert self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_public_different_nick(self):
        msg = Mock(is_public=True)
        opts = {
            'BOTNICK': '@' + self.ext.bot.nick,
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_nick_with_comma(self):
        msg = Mock(is_public=True)
        opts = {
            'BOTNICK': self.ext.bot.nick + ',',
            'foo': True
        }

        assert self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_nick_with_colon(self):
        msg = Mock(is_public=True)
        opts = {
            'BOTNICK': self.ext.bot.nick + ':',
            'foo': True
        }

        assert self.ext.should_handle_message(opts, msg)

    def test_should_handle_message_nick_with_diff_nick_ending(self):
        msg = Mock(is_public=True)
        opts = {
            'BOTNICK': self.ext.bot.nick + 't',
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, msg)
