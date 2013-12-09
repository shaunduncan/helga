from mock import patch, Mock

from helga.plugins import manager


@patch('helga.plugins.manager.db')
def test_auto_enable_plugins(db):
    client = Mock()
    rec = {'plugin': 'haiku', 'channels': ['a', 'b', 'c']}
    db.auto_enabled_plugins.find.return_value = [rec]

    manager.auto_enable_plugins(client)
    client.plugins.enable.assertCalledWith('a', 'haiku')
    client.plugins.enable.assertCalledWith('b', 'haiku')
    client.plugins.enable.assertCalledWith('c', 'haiku')


def test_list_plugins():
    client = Mock()
    client.plugins.plugins = {
        'plugin1': [1, 2, 3],
        'plugin2': [4, 5, 6],
        'plugin3': [7, 8, 9],
    }
    client.plugins.all_plugins = set(client.plugins.plugins.keys())
    client.plugins.enabled_plugins = {'foo': set(['plugin2'])}

    resp = manager.list_plugins(client, 'foo')
    assert 'Plugins enabled on this channel: plugin2' in resp
    assert 'Available plugins: plugin1, plugin3' in resp


@patch('helga.plugins.manager.db')
def test_enable_plugins_inits_record(db):
    client = Mock()
    db.auto_enabled_plugins.find.return_value = None
    manager.enable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.insert.called


@patch('helga.plugins.manager.db')
def test_enable_plugins_updates_record(db):
    client = Mock()
    rec = {'plugin': 'foobar', 'channels': ['#all']}
    db.auto_enabled_plugins.find.return_value = rec
    manager.enable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.save.called
    assert '#bots' in rec['channels']


@patch('helga.plugins.manager.db')
def test_disable_plugins(db):
    client = Mock()
    rec = {'plugin': 'foobar', 'channels': ['#all', '#bots']}
    db.auto_enabled_plugins.find.return_value = rec
    manager.disable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.save.called
    assert '#bots' not in rec['channels']
