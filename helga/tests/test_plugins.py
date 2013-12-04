"""
Tests for helga.plugins
"""
from unittest import TestCase

from mock import Mock

from helga import plugins


class CommandTestCase(TestCase):

    def setUp(self):
        self.cmd = plugins.Command('foo', aliases=('bar', 'baz'), help='foo cmd')

    def test_init_does_not_overwrite_things(self):
        class MyCommand(plugins.Command):
            command = 'dothis'
            aliases = ('foo', 'bar', 'baz')
            help = 'my command'

        cmd = MyCommand()
        assert cmd.command == 'dothis'
        assert cmd.aliases == ('foo', 'bar', 'baz')
        assert cmd.help == 'my command'

    def test_parse_handles_main_command(self):
        assert 'foo' == self.cmd.parse('helga foo')[0]

    def test_parse_handles_aliases(self):
        assert 'bar' == self.cmd.parse('helga bar')[0]
        assert 'baz' == self.cmd.parse('helga baz')[0]

    def test_parse_with_punctuation(self):
        assert 'foo' == self.cmd.parse('helga: foo')[0]
        assert 'foo' == self.cmd.parse('helga, foo')[0]
        assert 'foo' == self.cmd.parse('helga ----> foo')[0]

    def test_parse_does_not_handle(self):
        assert '' == self.cmd.parse('helga qux')[0]

    def test_parse_returns_args(self):
        assert ['1', '2', '3'] == self.cmd.parse('helga foo 1 2 3')[1]

    def test_process_for_different_command_returns_none(self):
        assert self.cmd.process('#bots', 'me', 'helga qux') is None

    def test_process_calls_class_run_method(self):
        self.cmd.run = lambda chan, nick, msg, cmd, args: 'run'
        assert 'run' == self.cmd.process('#bots', 'me', 'helga foo')

    def test_process_returns_none_when_typeerror(self):
        self.cmd.run = Mock(side_effect=TypeError)
        assert self.cmd.process('#bots', 'me', 'helga foo') is None

    def test_process_calls_custom_runner(self):
        cmd = plugins.Command('foo', aliases=('bar', 'baz'), help='foo command')
        cmd.run = lambda chan, nick, msg, cmd, args: 'runner'
        assert 'runner' == cmd.process('#bots', 'me', 'helga foo')

    def test_decorator_using_command(self):
        @plugins.command('foo')
        def foo(chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo('#bots', 'me', 'helga foo')

    def test_decorator_using_alias(self):
        @plugins.command('foo', aliases=['baz'])
        def foo(chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo('#bots', 'me', 'helga baz')


class MatchTestCase(TestCase):

    def setUp(self):
        self.match = plugins.Match('foo')

    def test_init_does_not_overwrite_things(self):
        class MyMatch(plugins.Match):
            pattern = 'foo'

        match = MyMatch()
        assert match.pattern == 'foo'

    def test_match_using_callable(self):
        self.match.pattern = lambda m: 'foobar'
        assert 'foobar' == self.match.match('this is a foo message')

    def test_match_using_simple_pattern(self):
        self.match.pattern = r'foo-(\d+)'
        assert ['123'] == self.match.match('this is about foo-123')

    def test_match_returns_none_on_typeerror(self):
        self.match.pattern = Mock(side_effect=TypeError)
        assert self.match.match('this is a foo message') is None

    def test_simple_decorator(self):
        @plugins.match('foo-(\d+)')
        def foo(chan, nick, msg, matches):
            return matches[0]

        assert '123' == foo('#bots', 'me', 'this is about foo-123')

    def test_callable_decorator(self):
        @plugins.match(lambda x: x.startswith('foo'))
        def foo(chan, nick, msg, matches):
            return 'bar'

        assert 'bar' == foo('#bots', 'me', 'foo at the start')
        assert foo('#bots', 'me', 'not at the start foo') is None
