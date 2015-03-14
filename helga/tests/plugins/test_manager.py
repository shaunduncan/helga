# -*- coding: utf8 -*-
from mock import call, patch, Mock

from helga.plugins import manager


@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_auto_enable_plugins(plugins, db):
    client = Mock()
    rec = {'plugin': 'haiku', 'channels': ['a', 'b', 'c']}
    db.auto_enabled_plugins.find.return_value = [rec]
    plugins.all_plugins = ['haiku']

    manager.auto_enable_plugins(client)
    assert plugins.enable.call_args_list == [
        call('a', 'haiku'),
        call('b', 'haiku'),
        call('c', 'haiku'),
    ]


@patch('helga.plugins.manager.registry')
def test_list_plugins(plugins):
    client = Mock()
    plugins.all_plugins = set(['plugin1', 'plugin2', 'plugin3'])
    plugins.enabled_plugins = {'foo': set(['plugin2'])}

    resp = manager.list_plugins(client, 'foo')
    assert 'Plugins enabled on this channel: plugin2' in resp
    assert 'Available plugins: plugin1, plugin3' in resp


@patch('helga.plugins.manager.registry')
def test_list_plugins_handles_unicode(plugins):
    client = Mock()
    snowman = u'☃'
    poo = u'💩'

    plugins.all_plugins = set([snowman, poo])
    plugins.enabled_plugins = {'foo': set([poo])}

    resp = manager.list_plugins(client, 'foo')
    assert u'Plugins enabled on this channel: {0}'.format(poo) in resp
    assert u'Available plugins: {0}'.format(snowman) in resp


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


@patch('helga.plugins.manager._filter_valid')
def test_enable_plugins_no_plugins(filter_valid):
    snowman = u'☃'
    filter_valid.return_value = []
    plugins = ['foo', 'bar', snowman]  # Test unicode

    resp = manager.enable_plugins(None, None, *plugins)
    expect = u"Sorry, but I don't know about these plugins: {0}, {1}, {2}".format('foo', 'bar', snowman)
    assert resp == expect


@patch('helga.plugins.manager._filter_valid')
@patch('helga.plugins.manager.db')
@patch('helga.plugins.manager.registry')
def test_disable_plugins(plugins, db, filter_valid):
    client = Mock()
    plugins.all_plugins = ['foobar', 'blah', 'no_record']
    filter_valid.return_value = plugins.all_plugins

    records = [
        {
            # This will be removed
            'plugin': 'foobar',
            'channels': ['#all', '#bots']
        },
        {
            # Not enabled for the channel
            'plugin': 'blah',
            'channels': ['#other'],
        },
        None  # No plugin found
    ]

    db.auto_enabled_plugins.find_one.side_effect = records
    manager.disable_plugins(client, '#bots', *plugins.all_plugins)
    db.auto_enabled_plugins.save.assert_called_with(records[0])
    assert '#bots' not in records[0]['channels']


@patch('helga.plugins.manager._filter_valid')
def test_disable_plugins_no_plugins(filter_valid):
    snowman = u'☃'
    filter_valid.return_value = []
    plugins = ['foo', 'bar', snowman]  # Test unicode

    resp = manager.disable_plugins(None, None, *plugins)
    expect = u"Sorry, but I don't know about these plugins: {0}, {1}, {2}".format('foo', 'bar', snowman)
    assert resp == expect


@patch('helga.plugins.manager.disable_plugins')
@patch('helga.plugins.manager.enable_plugins')
@patch('helga.plugins.manager.list_plugins')
def test_manager_plugin(list, enable, disable):
    list.return_value = 'list'
    enable.return_value = 'enable'
    disable.return_value = 'disable'

    assert 'list' == manager.manager('client', '#bots', 'me', 'message', 'plugins', [])
    assert 'list' == manager.manager('client', '#bots', 'me', 'message', 'plugins', ['list'])
    assert 'enable' == manager.manager('client', '#bots', 'me', 'message', 'plugins', ['enable'])
    assert 'disable' == manager.manager('client', '#bots', 'me', 'message', 'plugins', ['disable'])
    assert manager.manager('client', '#bots', 'me', 'message', 'plugins', ['lol']) is None
