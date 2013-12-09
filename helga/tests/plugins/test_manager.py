from mock import patch, Mock

from helga.plugins import manager


@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_auto_enable_plugins(plugins, db):
    client = Mock()
    rec = {'plugin': 'haiku', 'channels': ['a', 'b', 'c']}
    db.auto_enabled_plugins.find.return_value = [rec]

    manager.auto_enable_plugins(client)
    plugins.enable.assertCalledWith('a', 'haiku')
    plugins.enable.assertCalledWith('b', 'haiku')
    plugins.enable.assertCalledWith('c', 'haiku')


@patch('helga.plugins.manager.registry')
def test_list_plugins(plugins):
    client = Mock()
    plugins.plugins = {
        'plugin1': [1, 2, 3],
        'plugin2': [4, 5, 6],
        'plugin3': [7, 8, 9],
    }
    plugins.all_plugins = set(plugins.plugins.keys())
    plugins.enabled_plugins = {'foo': set(['plugin2'])}

    resp = manager.list_plugins(client, 'foo')
    assert 'Plugins enabled on this channel: plugin2' in resp
    assert 'Available plugins: plugin1, plugin3' in resp


@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_enable_plugins_inits_record(plugins, db):
    client = Mock()

    plugins.all_plugins = ['foobar']

    db.auto_enabled_plugins.find_one.return_value = None
    manager.enable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.insert.called


@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_enable_plugins_updates_record(plugins, db):
    client = Mock()

    plugins.all_plugins = ['foobar']

    rec = {'plugin': 'foobar', 'channels': ['#all']}
    db.auto_enabled_plugins.find_one.return_value = rec
    manager.enable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.save.called
    assert '#bots' in rec['channels']


@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_disable_plugins(plugins, db):
    client = Mock()
    plugins.all_plugins = ['foobar']

    rec = {'plugin': 'foobar', 'channels': ['#all', '#bots']}
    db.auto_enabled_plugins.find_one.return_value = rec
    manager.disable_plugins(client, '#bots', 'foobar')

    assert db.auto_enabled_plugins.save.called
    assert '#bots' not in rec['channels']
