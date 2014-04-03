"""
Tests for helga.plugins
"""
from unittest import TestCase

from mock import Mock, patch
from pretend import stub

from helga import plugins


class RegistryTestCase(TestCase):

    def test_prioritized(self):
        fake_plugin = stub(name='foo', priority=50)
        fake_decorated = stub(_plugins=[
            stub(name='bar', priority=10),
            stub(name='baz', priority=0),
            stub(name='qux', priority=99),
        ])
        plugins.registry.plugins = {'foo': fake_plugin, 'bar': fake_decorated}
        plugins.registry.enabled_plugins['#bots'] = set(['foo', 'bar'])

        items = plugins.registry.prioritized('#bots')

        assert items[0].name == 'qux'
        assert items[1].name == 'foo'
        assert items[2].name == 'bar'
        assert items[3].name == 'baz'

    def test_prioritized_reversed(self):
        fake_plugin = stub(name='foo', priority=50)
        fake_decorated = stub(_plugins=[
            stub(name='bar', priority=10),
            stub(name='baz', priority=0),
            stub(name='qux', priority=99),
        ])
        plugins.registry.plugins = {'foo': fake_plugin, 'bar': fake_decorated}
        plugins.registry.enabled_plugins['#bots'] = set(['foo', 'bar'])

        items = plugins.registry.prioritized('#bots', high_to_low=False)

        assert items[3].name == 'qux'
        assert items[2].name == 'foo'
        assert items[1].name == 'bar'
        assert items[0].name == 'baz'

    def test_process_stops_when_async(self):
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.return_value = None
        things[1].process.side_effect = plugins.ResponseNotReady
        things[2].process.return_value = None

        assert [] == plugins.registry.process(None, '#bots', 'me', 'foobar')
        assert not things[2].process.called


class PluginTestCase(TestCase):

    def setUp(self):
        self.plugin = plugins.Plugin()
        self.client = Mock(nickname='helga')

    def test_preprocessor_decorator(self):
        @plugins.preprocessor
        def foo(client, channel, nick, message):
            return 'foo', 'bar', 'baz'

        expected = ('foo', 'bar', 'baz')
        args = (self.client, '#bots', 'me', 'foobar')

        assert hasattr(foo, '_plugins')
        assert len(foo._plugins) == 1
        assert expected == foo(*args)
        assert expected == foo._plugins[0].preprocess(*args)


class CommandTestCase(TestCase):

    def setUp(self):
        self.cmd = plugins.Command('foo', aliases=('bar', 'baz'), help='foo cmd')
        self.client = Mock(nickname='helga')

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
        assert 'foo' == self.cmd.parse('helga', 'helga foo')[0]

    @patch('helga.plugins.core.settings')
    def test_parse_handles_char_prefix(self, settings):
        settings.COMMAND_PREFIX_CHAR = '#'
        assert 'foo' == self.cmd.parse('helga', '#foo')[0]

    def test_parse_handles_aliases(self):
        assert 'bar' == self.cmd.parse('helga', 'helga bar')[0]
        assert 'baz' == self.cmd.parse('helga', 'helga baz')[0]

    def test_parse_with_punctuation(self):
        assert 'foo' == self.cmd.parse('helga', 'helga: foo')[0]
        assert 'foo' == self.cmd.parse('helga', 'helga, foo')[0]
        assert 'foo' == self.cmd.parse('helga', 'helga ----> foo')[0]

    def test_parse_does_not_handle(self):
        assert '' == self.cmd.parse('helga', 'helga qux')[0]

    def test_parse_returns_args(self):
        assert ['1', '2', '3'] == self.cmd.parse('helga', 'helga foo 1 2 3')[1]

    def test_parse_handles_longest_command_first(self):
        with patch.object(self.cmd, 'aliases', ['b', 'bar']):
            for check in ('b', 'bar'):
                cmd, args = self.cmd.parse('helga', 'helga %s baz' % check)
                assert cmd == check
                assert args == ['baz']

    def test_process_for_different_command_returns_none(self):
        assert self.cmd.process(self.client, '#bots', 'me', 'helga qux') is None

    def test_process_calls_class_run_method(self):
        self.cmd.run = lambda client, chan, nick, msg, cmd, args: 'run'
        assert 'run' == self.cmd.process(self.client, '#bots', 'me', 'helga foo')

    def test_process_calls_custom_runner(self):
        cmd = plugins.Command('foo', aliases=('bar', 'baz'), help='foo command')
        cmd.run = lambda client, chan, nick, msg, cmd, args: 'runner'
        assert 'runner' == cmd.process(self.client, '#bots', 'me', 'helga foo')

    def test_multiple_decorators(self):
        @plugins.command('foo')
        @plugins.command('bar')
        def foobar(*args):
            return args[-2]

        assert len(foobar._plugins) == 2
        assert 'bar' == foobar._plugins[0](self.client, '#bots', 'me', 'helga bar')
        assert 'foo' == foobar._plugins[1](self.client, '#bots', 'me', 'helga foo')

    def test_decorator_using_command(self):
        @plugins.command('foo')
        def foo(client, chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'helga foo')

    def test_decorator_using_alias(self):
        @plugins.command('foo', aliases=['baz'])
        def foo(client, chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'helga baz')


class MatchTestCase(TestCase):

    def setUp(self):
        self.match = plugins.Match('foo')
        self.client = Mock()

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
        def foo(client, chan, nick, msg, matches):
            return matches[0]

        assert '123' == foo._plugins[0](self.client, '#bots', 'me', 'this is about foo-123')

    def test_callable_decorator(self):
        @plugins.match(lambda x: x.startswith('foo'))
        def foo(client, chan, nick, msg, matches):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'foo at the start')
        assert foo._plugins[0](self.client, '#bots', 'me', 'not at the start foo') is None
