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
    client.me.assertCalledWith('#bots', 'whispers to me')


@patch('helga.plugins.help.registry')
def test_help_gets_object_help_attrs(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub()

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin"

    client.msg.assertCalledWith('me', output)


@patch('helga.plugins.help.registry')
def test_help_gets_decorated_help_attrs(plugins):
    foo_plugin = stub(help='foo plugin')
    foo_fn = stub(_plugins=[foo_plugin])

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo']}
    plugins.plugins = {'foo': [foo_fn]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin"

    client.msg.assertCalledWith('me', output)


@patch('helga.plugins.help.registry')
def test_help_gets_multi_decorated_help_attrs(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')
    foo_fn = stub(_plugins=[foo_plugin, bar_plugin])

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo']}
    plugins.plugins = {'foo': [foo_fn]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin\nbar plugin"

    client.msg.assertCalledWith('me', output)


@patch('helga.plugins.help.registry')
def test_help_gets_single_plugin(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    help.help(client, '#bots', 'me', 'help', 'help', ['bar'])
    output = "me, here are the plugins I know about\nbar\nbar plugin"

    client.msg.assertCalledWith('me', output)


@patch('helga.plugins.help.registry')
def test_help_single_returns_unknown(plugins):
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')

    client = Mock()
    plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    resp = help.help(client, '#bots', 'me', 'help', 'help', ['baz'])

    assert resp == "Sorry me, I don't know about that plugin"
    assert not client.msg.called
