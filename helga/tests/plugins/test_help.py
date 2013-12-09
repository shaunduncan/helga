from mock import MagicMock as Mock
from pretend import stub

from helga.plugins import help


def test_help_should_whisper():
    client = Mock()
    help.help(client, '#bots', 'me', 'foo', 'bar', [])

    assert client.me.called
    client.me.assertCalledWith('#bots', 'whispers to me')


def test_help_gets_object_help_attrs():
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub()

    client = Mock()
    client.plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    client.plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin"

    client.msg.assertCalledWith('me', output)


def test_help_gets_decorated_help_attrs():
    foo_plugin = stub(help='foo plugin')
    foo_fn = stub(_plugins=[foo_plugin])

    client = Mock()
    client.plugins.enabled_plugins = {'#bots': ['foo']}
    client.plugins.plugins = {'foo': [foo_fn]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin"

    client.msg.assertCalledWith('me', output)


def test_help_gets_multi_decorated_help_attrs():
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')
    foo_fn = stub(_plugins=[foo_plugin, bar_plugin])

    client = Mock()
    client.plugins.enabled_plugins = {'#bots': ['foo']}
    client.plugins.plugins = {'foo': [foo_fn]}

    help.help(client, '#bots', 'me', 'help', 'help', [])
    output = "me, here are the plugins I know about\nfoo\nfoo plugin\nbar plugin"

    client.msg.assertCalledWith('me', output)


def test_help_gets_single_plugin():
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')

    client = Mock()
    client.plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    client.plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    help.help(client, '#bots', 'me', 'help', 'help', ['bar'])
    output = "me, here are the plugins I know about\nbar\nbar plugin"

    client.msg.assertCalledWith('me', output)


def test_help_single_returns_unknown():
    foo_plugin = stub(help='foo plugin')
    bar_plugin = stub(help='bar plugin')

    client = Mock()
    client.plugins.enabled_plugins = {'#bots': ['foo', 'bar']}
    client.plugins.plugins = {'foo': [foo_plugin], 'bar': [bar_plugin]}

    resp = help.help(client, '#bots', 'me', 'help', 'help', ['baz'])

    assert resp == "Sorry me, I don't know about that plugin"
    assert not client.msg.called
