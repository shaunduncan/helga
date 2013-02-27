from unittest import TestCase

from helga.extensions.base import (CommandExtension,
                                   ContextualExtension)
from helga.tests.util import mock_bot


class ContextualExtensionTestCase(TestCase):

    def setUp(self):
        self.ext = ContextualExtension(mock_bot())

    def test_contextualize_not_found(self):
        self.ext.context = r'foo'
        assert self.ext.contextualize('bar') is None

    def test_contextualize_returns_many(self):
        self.ext.allow_many = True
        self.ext.context = r'foo[\d]+'
        self.ext.response_fmt = '%(response)s'

        resp = self.ext.contextualize('two things: foo1 and foo2')
        assert resp == 'foo1, foo2'

    def test_contextualize_returns_one(self):
        self.ext.allow_many = False
        self.ext.context = r'foo[\d]+'
        self.ext.response_fmt = '%(response)s'

        resp = self.ext.contextualize('two things: foo1 and foo2')
        assert resp == 'foo1'


class CommandExtensionTestCase(TestCase):

    def setUp(self):
        self.ext = CommandExtension(mock_bot())

    def test_parse_command(self):
        self.ext.usage = '[FOO] [BAR] [BAZ]'

        opts = self.ext.parse_command('foo bar baz')
        assert opts['FOO'] == 'foo'
        assert opts['BAR'] == 'bar'
        assert opts['BAZ'] == 'baz'

    def test_parse_command_no_match(self):
        self.ext.usage = 'foo [BAR]'
        assert self.ext.parse_command('helga dosomething') is None

    def test_parse_command_no_nick_required_arg(self):
        self.ext.usage = '[BOTNICK] foo'
        opts = self.ext.parse_command('foo')
        assert opts

    def test_should_handle_message_private_without_nick(self):
        opts = {
            'foo': True
        }

        assert self.ext.should_handle_message(opts, False)

    def test_should_handle_message_private_with_nick(self):
        opts = {
            'BOTNICK': self.ext.bot.nick,
            'foo': True
        }

        assert self.ext.should_handle_message(opts, False)

    def test_should_handle_message_private_different_nick(self):
        opts = {
            'BOTNICK': '@' + self.ext.bot.nick,
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, False)

    def test_should_handle_message_public_without_nick(self):
        opts = {
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, True)

    def test_should_handle_message_public_with_nick(self):
        opts = {
            'BOTNICK': self.ext.bot.nick,
            'foo': True
        }

        assert self.ext.should_handle_message(opts, True)

    def test_should_handle_message_public_different_nick(self):
        opts = {
            'BOTNICK': '@' + self.ext.bot.nick,
            'foo': True
        }

        assert not self.ext.should_handle_message(opts, True)
