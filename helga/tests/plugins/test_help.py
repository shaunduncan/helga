# -*- coding: utf8 -*-
from collections import defaultdict
from mock import MagicMock as Mock, patch
from pretend import stub

from helga.plugins import help


@patch('helga.plugins.help.registry')
def test_help_should_whisper(plugins):
    client = Mock()
    plugins.enabled_plugins = defaultdict(list)
    plugins.plugins = {}

    help.help(client, '#bots', 'me', 'foo', 'bar', [])

    assert client.me.called
    client.me.assert_called_with('#bots', 'whispers to me')


@patch('helga.plugins.help.registry')
def test_help_gets_object_help_attrs(plugins):
    snowman = u'☃'
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub()
    uni_plugin = stub(help=u'unicode plugin {0}'.format(snowman))

    client = Mock()
    plugins.enabled_plugins = {
        '#bots': ['foo', 'bar', snowman],
    }
    plugins.plugins = {
        'foo': foo_plugin,
        'bar': bar_plugin,
        snowman: uni_plugin,
    }

    help.help(client, '#bots', 'me', 'help', 'help', [])

    nick, message = client.msg.call_args[0]
    assert nick == 'me'
    assert 'me, here are the plugins I know about' in message
    assert u'[{0}] unicode plugin {0}'.format(snowman) in message
    assert '[foo] foo plugin' in message


@patch('helga.plugins.help.registry')
def test_help_gets_decorated_help_attrs(plugins):
    snowman = u'☃'
    foo_plugin = stub(help='foo plugin')
    foo_fn = stub(_plugins=[foo_plugin])

    uni_plugin = stub(help=u'unicode plugin {0}'.format(snowman))
    uni_fn = stub(_plugins=[uni_plugin])

    client = Mock()
    plugins.enabled_plugins = {
        '#bots': ['foo', snowman],
    }
    plugins.plugins = {
        'foo': foo_fn,
        snowman: uni_fn,
    }

    help.help(client, '#bots', 'me', 'help', 'help', [])

    nick, message = client.msg.call_args[0]
    assert nick == 'me'
    assert 'me, here are the plugins I know about' in message
    assert u'[{0}] unicode plugin {0}'.format(snowman) in message
    assert '[foo] foo plugin' in message


@patch('helga.plugins.help.registry')
def test_help_gets_multi_decorated_help_attrs(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')
    uni_plugin = stub(help=u'unicode plugin ☃')
    foo_fn = stub(_plugins=[foo_plugin, bar_plugin, uni_plugin])

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo']}
    plugins.plugins = {'foo': foo_fn}

    help.help(client, '#bots', 'me', 'help', 'help', [])

    nick, message = client.msg.call_args[0]
    assert nick == 'me'
    assert 'me, here are the plugins I know about' in message
    assert u'[foo] foo plugin. bar plugin. unicode plugin ☃' in message


@patch('helga.plugins.help.registry')
def test_help_gets_single_plugin(plugins):
    snowman = u'☃'
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')
    uni_plugin = stub(help=u'unicode plugin {0}'.format(snowman))

    client = Mock()
    plugins.enabled_plugins = {
        '#bots': ['foo', 'bar', snowman],
    }
    plugins.plugins = {
        'foo': foo_plugin,
        'bar': bar_plugin,
        snowman: uni_plugin,
    }

    message = help.help(client, '#bots', 'me', 'help', 'help', ['bar'])
    assert '[bar] bar plugin' in message
    assert '[foo] foo plugin' not in message
    assert u'[{0}] unicode plugin {0}'.format(snowman) not in message

    message = help.help(client, '#bots', 'me', 'help', 'help', [snowman])
    assert '[bar] bar plugin' not in message
    assert '[foo] foo plugin' not in message
    assert u'[{0}] unicode plugin {0}'.format(snowman) in message


@patch('helga.plugins.help.registry')
def test_help_single_returns_unknown(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')

    client = Mock()
    plugins.enabled_plugins = {
        '#bots': ['foo', 'bar'],
    }
    plugins.plugins = {
        'foo': foo_plugin,
        'bar': bar_plugin,
    }

    resp = help.help(client, '#bots', 'me', 'help', 'help', ['baz'])
    assert resp == "Sorry me, I don't know about that plugin"
    assert not client.msg.called

    # Can handle unicode
    resp = help.help(client, '#bots', 'me', 'help', 'help', [u'☃'])
    assert resp == "Sorry me, I don't know about that plugin"
    assert not client.msg.called


@patch('helga.plugins.help.registry')
def test_help_with_unloaded_plugin(plugins):
    snowman = u'☃'
    foo_plugin = stub(help='foo plugin')

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', snowman]}
    plugins.plugins = {'foo': foo_plugin}

    resp = help.help(client, '#bots', 'me', 'help', 'help', [snowman])
    assert resp == u"Sorry me, there's no help string for plugin '{0}'".format(snowman)
    assert not client.msg.called


@patch('helga.plugins.help.registry')
def test_help_object_with_empty_help_attr(plugins):
    foo_plugin = stub(help='')
    uni_plugin = stub(help='')

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', u'☃']}
    plugins.plugins = {'foo': foo_plugin, u'☃': uni_plugin}

    help.help(client, '#bots', 'me', 'help', 'help', [])

    _, message = client.msg.call_args[0]
    assert '[foo] No help string for this plugin' in message
    assert u'[☃] No help string for this plugin' in message


@patch('helga.plugins.help.registry')
def test_help_decorated_with_empty_help_attr(plugins):
    foo_fn = stub(_plugins=[stub(help='')])
    uni_fn = stub(_plugins=[stub(help='')])

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', u'☃']}
    plugins.plugins = {'foo': foo_fn, u'☃': uni_fn}

    help.help(client, '#bots', 'me', 'help', 'help', [])

    _, message = client.msg.call_args[0]
    assert '[foo] No help string for this plugin' in message
    assert u'[☃] No help string for this plugin' in message


def test_format_help_string():
    unistr = u'[☃] snowman. ☃'
    string = '[foo] just foo. bar'

    assert unistr == help.format_help_string(u'☃', 'snowman', u'☃')
    assert string == help.format_help_string('foo', 'just foo', 'bar')
