# -*- coding: utf8 -*-
"""
Tests for helga.plugins
"""
from collections import defaultdict

import pytest

from mock import Mock, call, patch
from pretend import stub

from helga import settings
from helga.plugins import (Command,
                           Match,
                           Plugin,
                           Registry,
                           ResponseNotReady,
                           command,
                           match,
                           preprocessor,
                           registry)


class TestRegistry(object):

    def setup(self):
        registry.plugins = {}
        registry.enabled_plugins = defaultdict(set)

        def foo():
            pass
        foo._plugins = []

        def bar():
            pass

        class Foo(Plugin):
            pass

        class Bar(object):
            pass

        self.valid_plugins = [foo, Foo, Foo()]
        self.invalid_plugins = [bar, Bar, Bar()]

        # For testing unicode compatibility
        self.snowman = u'☃'

    def _make_mock(self, **attrs):
        m = Mock()
        for k, v in attrs.iteritems():
            setattr(m, k, v)
        return m

    @pytest.mark.parametrize('setting,expected', [
        (True, set(('foo', 'bar', 'baz'))),
        (False, set()),
        (None, set()),
        (['foo', 'bar'], set(('foo', 'bar'))),
    ])
    def test_whitelist_setup(self, setting, expected):
        entry_points = [
            self._make_mock(name='foo'),
            self._make_mock(name='bar'),
            self._make_mock(name='baz'),
        ]

        with patch('helga.plugins.pkg_resources') as pkg_resources:
            with patch('helga.plugins.settings') as settings:
                settings.ENABLED_PLUGINS = setting
                settings.DISABLED_PLUGINS = False

                pkg_resources.iter_entry_points.return_value = entry_points

                with patch.object(Registry, '_Registry__instance', None):
                    reg = Registry()
                    assert reg.whitelist_plugins == expected

    @pytest.mark.parametrize('setting,expected', [
        (True, set(('foo', 'bar', 'baz'))),
        (False, set()),
        (None, set()),
        (['foo', 'bar'], set(('foo', 'bar'))),
    ])
    def test_blacklist_setup(self, setting, expected):
        entry_points = [
            self._make_mock(name='foo'),
            self._make_mock(name='bar'),
            self._make_mock(name='baz'),
        ]

        with patch('helga.plugins.pkg_resources') as pkg_resources:
            with patch('helga.plugins.settings') as settings:
                settings.ENABLED_PLUGINS = True
                settings.DISABLED_PLUGINS = setting

                pkg_resources.iter_entry_points.return_value = entry_points

                with patch.object(Registry, '_Registry__instance', None):
                    reg = Registry()
                    assert reg.blacklist_plugins == expected

    @pytest.mark.parametrize('whitelist,blacklist,expected', [
        (True, True, set()),
        (True, None, set(('foo', 'bar', 'baz'))),
        (['foo', 'bar', 'baz'], None, set(('foo', 'bar', 'baz'))),
        (['foo', 'bar', 'baz'], ['foo', 'bar', 'baz'], set()),
        (['foo', 'bar', 'baz'], ['foo'], set(('bar', 'baz'))),
        (None, ['foo', 'bar', 'baz'], set()),
    ])
    def test_default_channel_plugins_setup(self, whitelist, blacklist, expected):
        entry_points = [
            self._make_mock(name='foo'),
            self._make_mock(name='bar'),
            self._make_mock(name='baz'),
        ]

        with patch('helga.plugins.pkg_resources') as pkg_resources:
            with patch('helga.plugins.settings') as settings:
                settings.ENABLED_PLUGINS = whitelist
                settings.DISABLED_PLUGINS = blacklist
                settings.DEFAULT_CHANNEL_PLUGINS = ['foo', 'bar', 'baz']

                pkg_resources.iter_entry_points.return_value = entry_points

                with patch.object(Registry, '_Registry__instance', None):
                    reg = Registry()
                    assert reg.default_channel_plugins == expected

    def test_prioritized(self):
        fake_plugin = stub(name='foo', priority=50)
        fake_decorated = stub(_plugins=[
            stub(name='bar', priority=10),
            stub(name='baz', priority=0),
            stub(name=self.snowman, priority=99),
        ])
        registry.plugins = {'foo': fake_plugin, 'bar': fake_decorated}
        registry.enabled_plugins['#bots'] = set(['foo', 'bar'])

        items = registry.prioritized('#bots')

        assert items[0].name == self.snowman
        assert items[1].name == 'foo'
        assert items[2].name == 'bar'
        assert items[3].name == 'baz'

    def test_prioritized_reversed(self):
        fake_plugin = stub(name='foo', priority=50)
        fake_decorated = stub(_plugins=[
            stub(name='bar', priority=10),
            stub(name='baz', priority=0),
            stub(name=self.snowman, priority=99),
        ])
        registry.plugins = {'foo': fake_plugin, 'bar': fake_decorated}
        registry.enabled_plugins['#bots'] = set(['foo', 'bar'])

        items = registry.prioritized('#bots', high_to_low=False)

        assert items[3].name == self.snowman
        assert items[2].name == 'foo'
        assert items[1].name == 'bar'
        assert items[0].name == 'baz'

    def test_prioritized_ignores_missing_plugin(self):
        fake_plugin = stub(name='foo', priority=50)
        registry.plugins = {'foo': fake_plugin}
        registry.enabled_plugins['#bots'] = set(['foo', 'bar'])

        items = registry.prioritized('#bots')

        assert len(items) == 1
        assert items[0].name == 'foo'

    def test_process_stops_when_async(self):
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.return_value = None
        things[1].process.side_effect = ResponseNotReady
        things[2].process.return_value = None

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = things
            assert [] == registry.process(None, '#bots', 'me', 'foobar')
            assert things[1].process.called
            assert not things[2].process.called

    def test_process_async_honors_all_responses(self):
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.return_value = None
        things[1].process.side_effect = ResponseNotReady
        things[2].process.return_value = None

        with patch.object(registry, 'prioritized') as prio:
            with patch.object(settings, 'PLUGIN_FIRST_RESPONDER_ONLY', False):
                prio.return_value = things
                assert [] == registry.process(None, '#bots', 'me', 'foobar')
                assert things[0].process.called
                assert things[1].process.called
                assert things[2].process.called

    def test_process_async_honors_first_response(self):
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.side_effect = ResponseNotReady
        things[1].process.return_value = None
        things[2].process.return_value = None

        with patch.object(registry, 'prioritized') as prio:
            with patch.object(settings, 'PLUGIN_FIRST_RESPONDER_ONLY', True):
                prio.return_value = things
                assert [] == registry.process(None, '#bots', 'me', 'foobar')
                assert things[0].process.called
                assert not things[1].process.called
                assert not things[2].process.called

    def test_process_returns_all_responses(self):
        settings.PLUGIN_FIRST_RESPONDER_ONLY = False
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.return_value = ['foo', 'bar', None]
        things[1].process.return_value = self.snowman
        things[2].process.return_value = 'baz'

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = things
            response = registry.process(None, '#bots', 'me', 'foobar')
            assert response == [u'foo', u'bar', self.snowman, u'baz']

    def test_process_returns_first_response(self):
        settings.PLUGIN_FIRST_RESPONDER_ONLY = True
        things = [Mock(), Mock(), Mock()]

        # Make the middle one raise
        things[0].process.return_value = ['foo', 'bar', None]
        things[1].process.return_value = self.snowman
        things[2].process.return_value = 'baz'

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = things
            response = registry.process(None, '#bots', 'me', 'foobar')
            assert response == [u'foo', u'bar']

    def test_process_returns_unicode(self):
        plugin = Mock()
        plugin.process.return_value = ['foo', 'bar', self.snowman]

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = [plugin]
            responses = registry.process('', '', '', '')
            assert all(map(lambda x: isinstance(x, unicode), responses))

    def test_process_ignores_exception(self):
        settings.PLUGIN_FIRST_RESPONDER_ONLY = True
        things = [Mock(), Mock()]

        # Make the middle one raise
        things[0].process.side_effect = Exception
        things[1].process.return_value = 'foo'

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = things
            response = registry.process(None, '#bots', 'me', 'foobar')
            assert response == [u'foo']

    def test_registry_is_singleton(self):
        assert id(Registry()) == id(Registry())

    def test_register_raises_typeerror(self):
        for plugin in self.invalid_plugins:
            with pytest.raises(TypeError):
                registry.register('invalid', plugin)

    def test_register_valid_plugins(self):
        for plugin in self.valid_plugins:
            registry.register(repr(plugin), plugin)
            assert repr(plugin) in registry.plugins

    def test_register_plugin_handles_unicode(self):
        for plugin in self.invalid_plugins:
            with pytest.raises(TypeError):
                registry.register('invalid', plugin)

        for plugin in self.valid_plugins:
            name = u'{0}-{1}'.format(self.snowman, repr(plugin))
            registry.register(name, plugin)
            assert name in registry.plugins

    def test_all_plugins(self):
        registry.register('foo', self.valid_plugins[0])
        assert set(['foo']) == registry.all_plugins

    def test_get_plugin(self):
        registry.register('foo', self.valid_plugins[0])
        registry.register(self.snowman, self.valid_plugins[0])
        assert self.valid_plugins[0] == registry.get_plugin('foo')
        assert self.valid_plugins[0] == registry.get_plugin(self.snowman)

    def test_get_plugin_returns_none(self):
        assert registry.get_plugin('foo') is None

    def test_enable(self):
        assert 'foo' not in registry.enabled_plugins['#foo']
        assert self.snowman not in registry.enabled_plugins['#foo']
        registry.enable('#foo', 'foo', self.snowman)
        assert 'foo' in registry.enabled_plugins['#foo']
        assert self.snowman in registry.enabled_plugins['#foo']

    def test_disable(self):
        registry.enable('#foo', 'foo', self.snowman)
        assert 'foo' in registry.enabled_plugins['#foo']
        assert self.snowman in registry.enabled_plugins['#foo']
        registry.disable('#foo', 'foo', self.snowman)
        assert 'foo' not in registry.enabled_plugins['#foo']
        assert self.snowman not in registry.enabled_plugins['#foo']

    @patch('helga.plugins.logger')
    @patch('helga.plugins.pkg_resources')
    @patch('helga.plugins.smokesignal')
    def test_load(self, signal, pkg_resources, logger):
        entry_points = [
            Mock(load=lambda: 'foo'),
            Mock(load=lambda: 'snowman'),
            Mock(),
        ]
        entry_points[0].name = 'foo'
        entry_points[1].name = self.snowman

        # Exceptions should not bomb the load process
        entry_points[2].name = 'bar'
        entry_points[2].load.side_effect = Exception

        pkg_resources.iter_entry_points.return_value = entry_points

        with patch.multiple(registry,
                            register=Mock(),
                            whitelist_plugins=set(['foo', self.snowman, 'bar']),
                            blacklist_plugins=set()):
            registry.load()
            registry.register.assert_has_calls([
                call('foo', 'foo'),
                call(self.snowman, 'snowman'),
            ])

            logger.exception.assert_called_with('Error initializing plugin %s', entry_points[2])

        # Ensure that we sent the signal
        signal.emit.assert_called_with('plugins_loaded')

    @patch('helga.plugins.pkg_resources')
    def test_load_with_no_whitelist(self, pkg_resources):
        entry_points = [
            Mock(),
            Mock(),
            Mock(),
        ]

        with patch.object(registry, 'whitelist_plugins', []):
            registry.load()
            assert not any([
                entry_points[0].load.called,
                entry_points[1].load.called,
                entry_points[2].load.called,
            ])

    @patch('helga.plugins.pkg_resources')
    def test_load_skips_blacklisted(self, pkg_resources):
        entry_points = [
            Mock(),
            Mock(),
            Mock(),
        ]

        entry_points[0].name = 'foo'
        entry_points[1].name = 'bar'
        entry_points[2].name = 'baz'

        whitelist = ['a', 'b', 'c']
        blacklist = ['foo', 'bar', 'baz']

        pkg_resources.iter_entry_points.return_value = entry_points

        with patch.multiple(registry, whitelist_plugins=whitelist, blacklist_plugins=blacklist):
            registry.load()
            assert not any([
                entry_points[0].load.called,
                entry_points[1].load.called,
                entry_points[2].load.called,
            ])

    @patch('helga.plugins.pkg_resources')
    def test_load_skips_non_whitelist(self, pkg_resources):
        entry_points = [
            Mock(),
            Mock(),
            Mock(),
        ]

        entry_points[0].name = 'foo'
        entry_points[1].name = 'bar'
        entry_points[2].name = 'baz'

        pkg_resources.iter_entry_points.return_value = entry_points

        whitelist = ['a', 'b', 'c']

        with patch.multiple(registry, whitelist_plugins=whitelist, blacklist_plugins=[]):
            registry.load()
            assert not any([
                entry_points[0].load.called,
                entry_points[1].load.called,
                entry_points[2].load.called,
            ])

    def test_reload_not_registered(self):
        assert 'Unknown plugin' in registry.reload('foo')
        assert 'Unknown plugin' in registry.reload(self.snowman)

    @patch('helga.plugins.pkg_resources')
    @patch('helga.plugins.sys')
    @patch('__builtin__.reload')
    def test_reload(self, reloader, sys, pkg_resources):
        entry_points = [
            Mock(module_name='foo', load=lambda: 'loaded'),
            Mock(module_name='snowman', load=lambda: 'loaded')
        ]
        entry_points[0].name = 'foo'
        entry_points[1].name = self.snowman
        pkg_resources.iter_entry_points.return_value = entry_points

        sys.modules = {
            'foo': entry_points[0],
            'snowman': entry_points[1],
        }

        registry.plugins = ['foo', self.snowman]

        for name in ('foo', self.snowman):
            with patch.object(registry, 'register') as register:
                assert registry.reload(name)
                register.assert_called_with(name, 'loaded')

    @patch('helga.plugins.pkg_resources')
    @patch('helga.plugins.sys')
    @patch('__builtin__.reload')
    def test_reload_returns_false_on_exception(self, reloader, sys, pkg_resources):
        module = Mock(module_name='foo')
        module.name = 'foo'
        module.load.side_effect = Exception

        entry_points = [module]
        pkg_resources.iter_entry_points.return_value = entry_points
        sys.modules = {'foo': module}
        registry.plugins = ['foo']

        with patch.object(registry, 'register') as register:
            assert not registry.reload('foo')
            assert not register.called

    def test_preprocess(self):
        plugins = [Mock(), Mock(), Mock()]

        # Raising an exception shouldn't affect the others
        plugins[0].preprocess.return_value = ('foo', 'bar', self.snowman)
        plugins[1].preprocess.side_effect = Exception
        plugins[2].preprocess.return_value = ('abc', 'def', 'ghi')

        with patch.object(registry, 'prioritized') as prio:
            prio.return_value = plugins

            # Return value is what the last plugin returns
            retval = registry.preprocess(None, '#bots', 'me', self.snowman)
            assert retval == ('abc', 'def', 'ghi')

            # Should receive what the first plugin changed
            plugins[2].preprocess.assert_called_with(None, 'foo', 'bar', self.snowman)

            # Exception raising preprocess should have at least been called
            assert plugins[1].preprocess.called


class TestPlugin(object):

    def setup(self):
        self.plugin = Plugin()
        self.client = Mock(nickname='helga')

    def test_preprocessor_decorator(self):
        @preprocessor
        def foo(client, channel, nick, message):
            return 'foo', 'bar', 'baz'

        expected = ('foo', 'bar', 'baz')
        args = (self.client, '#bots', 'me', 'foobar')

        assert hasattr(foo, '_plugins')
        assert len(foo._plugins) == 1
        assert expected == foo(*args)
        assert expected == foo._plugins[0].preprocess(*args)

    def test_preprocess_with_priority(self):
        @preprocessor(10)
        def foo(client, channel, nick, message):
            return 'foo', 'bar', 'baz'

        expected = ('foo', 'bar', 'baz')
        args = (self.client, '#bots', 'me', 'foobar')

        assert hasattr(foo, '_plugins')
        assert len(foo._plugins) == 1
        assert expected == foo(*args)
        assert expected == foo._plugins[0].preprocess(*args)
        assert 10 == foo._plugins[0].priority

    def test_base_plugin_process_calls_run(self):
        plugin = Plugin()
        with patch.object(plugin, 'run') as run:
            plugin.process('foo', 'bar', 'baz', 'qux')
            run.assert_called_with('foo', 'bar', 'baz', 'qux')


class TestCommand(object):

    def setup(self):
        self.cmd = Command('foo', aliases=('bar', 'baz'), help='foo cmd')
        self.client = Mock(nickname='helga')

    def test_init_does_not_overwrite_things(self):
        class MyCommand(Command):
            command = 'dothis'
            aliases = ('foo', 'bar', 'baz', 'f')
            help = 'my command'

        cmd = MyCommand()
        assert cmd.command == 'dothis'
        assert cmd.aliases == ('foo', 'bar', 'baz', 'f')
        assert cmd.help == 'my command'

    def test_parse_handles_main_command(self):
        assert 'foo' == self.cmd.parse('helga', 'helga foo')[0]

    @patch('helga.plugins.settings')
    def test_parse_handles_char_prefix(self, settings):
        settings.COMMAND_PREFIX_CHAR = '#'
        assert 'foo' == self.cmd.parse('helga', '#foo')[0]

    @patch('helga.plugins.settings')
    def test_parse_handles_botnick_string(self, settings):
        settings.COMMAND_PREFIX_BOTNICK = '@helga'
        settings.COMMAND_PREFIX_CHAR = ''
        assert 'foo' == self.cmd.parse('helga', '@helga foo')[0]

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

    def test_parse_does_not_handle_something_else(self):
        assert ('', []) == self.cmd.parse('helga', 'helga fun')

    def test_parse_handles_unicode(self):
        snowman = u'☃'
        disapproval = u'ಠ_ಠ'
        cmd = u'helga {0} {1}'.format(snowman, disapproval)
        self.cmd.command = snowman
        assert (snowman, [disapproval]) == self.cmd.parse('helga', cmd)

    @pytest.mark.parametrize('argstr,expected', [
        ('foo bar "baz qux"', ['foo', 'bar', 'baz qux']),
        (u'foo "bar ☃"', ['foo', u'bar ☃']),
    ])
    def test_parse_argstr_shlex(self, argstr, expected):
        with patch('helga.plugins.settings') as settings:
            settings.COMMAND_ARGS_SHLEX = True
            assert self.cmd._parse_argstr(argstr) == expected

    @pytest.mark.parametrize('argstr,expected', [
        ('foo bar "baz qux"', ['foo', 'bar', '"baz', 'qux"']),
        (u'foo "bar ☃"', ['foo', '"bar', u'☃"']),
    ])
    def test_parse_argstr_whitespace(self, argstr, expected):
        with patch('helga.plugins.settings') as settings:
            settings.COMMAND_ARGS_SHLEX = False
            assert self.cmd._parse_argstr(argstr) == expected

    def test_process_for_different_command_returns_none(self):
        assert self.cmd.process(self.client, '#bots', 'me', 'helga qux') is None

    def test_process_calls_class_run_method(self):
        self.cmd.run = lambda client, chan, nick, msg, cmd, args: 'run'
        assert 'run' == self.cmd.process(self.client, '#bots', 'me', 'helga foo')

    def test_process_calls_custom_runner(self):
        cmd = Command('foo', aliases=('bar', 'baz'), help='foo command')
        cmd.run = lambda client, chan, nick, msg, cmd, args: 'runner'
        assert 'runner' == cmd.process(self.client, '#bots', 'me', 'helga foo')

    def test_process_is_case_insensitive(self):
        with patch.object(self.cmd, 'run'):
            with patch.object(settings, 'COMMAND_IGNORECASE', True):
                settings.COMMAND_IGNORECASE = True
                self.cmd.run.return_value = 'run'
                assert 'run' == self.cmd.process(self.client, '#bots', 'me', 'HELGA FOO')

    def test_multiple_decorators(self):
        @command('foo')
        @command('bar')
        def foobar(*args):
            return args[-2]

        assert len(foobar._plugins) == 2
        assert 'bar' == foobar._plugins[0](self.client, '#bots', 'me', 'helga bar')
        assert 'foo' == foobar._plugins[1](self.client, '#bots', 'me', 'helga foo')

    def test_decorator_using_command(self):
        @command('foo')
        def foo(client, chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'helga foo')

    def test_decorator_using_alias(self):
        @command('foo', aliases=['baz'])
        def foo(client, chan, nick, msg, cmd, args):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'helga baz')

    def test_decorator_with_shlex(self):
        @command('foo', shlex=True)
        def foo(client, chan, nick, msg, cmd, args):
            return args

        with patch('helga.plugins.settings') as settings:
            settings.COMMAND_ARGS_SHLEX = False
            settings.COMMAND_PREFIX_BOTNICK = True
            settings.COMMAND_PREFIX_CHAR = '!'
            message = 'helga foo bar "baz qux"'
            assert foo._plugins[0](self.client, '#bots', 'me', message) == ['bar', 'baz qux']


class TestMatch(object):

    def setup(self):
        self.match = Match('foo')
        self.client = Mock()

    def test_init_does_not_overwrite_things(self):
        class MyMatch(Match):
            pattern = 'foo'

        m = MyMatch()
        assert m.pattern == 'foo'

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
        @match('foo-(\d+)')
        def foo(client, chan, nick, msg, matches):
            return matches[0]

        assert '123' == foo._plugins[0](self.client, '#bots', 'me', 'this is about foo-123')

    def test_callable_decorator(self):
        @match(lambda x: x.startswith('foo'))
        def foo(client, chan, nick, msg, matches):
            return 'bar'

        assert 'bar' == foo._plugins[0](self.client, '#bots', 'me', 'foo at the start')
        assert foo._plugins[0](self.client, '#bots', 'me', 'not at the start foo') is None

    def test_match_with_unicode(self):
        @match(u'☃')
        def snowman_match(client, chan, nick, msg, matches):
            return 'snowman'
        assert 'snowman' == snowman_match._plugins[0](self.client, '#bots', 'me', u'☃')


def test_custom_plugin_priorities(tmpdir):
    file = tmpdir.join('foo.py')
    file.write('\n'.join([
        'PLUGIN_PRIORITY_LOW = 1',
        'PLUGIN_PRIORITY_NORMAL = 42',
        'PLUGIN_PRIORITY_HIGH = 9000',
    ]))

    settings.configure(str(file))

    from helga import plugins
    reload(plugins)

    assert plugins.PRIORITY_LOW == 1
    assert plugins.PRIORITY_NORMAL == 42
    assert plugins.PRIORITY_HIGH == 9000
