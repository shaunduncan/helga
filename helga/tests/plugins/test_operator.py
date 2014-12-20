# -*- coding: utf8 -*-
from mock import Mock, patch, call
from pretend import stub

from helga.plugins import operator, ACKS


def test_operator_ignores_non_oper_user():
    client = stub(operators=['me'])
    formatted_nopes = map(lambda s: s.format(nick='sduncan'), operator.nopes)
    assert operator.operator(client, '#bots', 'sduncan', 'do something', '', '') in formatted_nopes


def test_operator_join_calls_client_join():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['join', '#foo'])
    client.join.assert_called_with('#foo')


def test_operator_join_ignores_invalid_channel():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['join', 'foo'])
    assert not client.join.called


def test_operator_leave_calls_client_leave():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['leave', '#foo'])
    client.leave.assert_called_with('#foo')


def test_operator_leave_ignores_invalid_channel():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['leave', 'foo'])
    assert not client.leave.called


@patch('helga.plugins.operator.reload_plugin')
@patch('helga.plugins.operator.remove_autojoin')
@patch('helga.plugins.operator.add_autojoin')
def test_operator_handles_subcmd(add_autojoin, remove_autojoin, reload_plugin):
    add_autojoin.return_value = 'add_autojoin'
    remove_autojoin.return_value = 'remove_autojoin'
    reload_plugin.return_value = 'reload_plugin'

    client = Mock(operators=['me'])
    args = [client, '#bots', 'me', 'message', 'operator']

    # Client commands
    for cmd in ('join', 'leave'):
        client.reset_mock()
        assert operator.operator(*(args + [[cmd, '#foo']])) is None
        getattr(client, cmd).assert_called_with('#foo')

    # Autojoin add/remove
    assert 'add_autojoin' == operator.operator(*(args + [['autojoin', 'add', '#foo']]))
    assert 'remove_autojoin' == operator.operator(*(args + [['autojoin', 'remove', '#foo']]))

    # The feature that shall not be named
    operator.operator(*(args + [['nsa', '#other_chan', 'unicode', 'snowman', u'☃']]))
    client.msg.assert_called_with('#other_chan', u'unicode snowman ☃')

    assert 'reload_plugin' == operator.operator(*(args + [['reload', 'foo']]))


@patch('helga.plugins.operator.db')
def test_add_autojoin_exists(db):
    db.autojoin.find.return_value = db
    db.count.return_value = 1
    assert operator.add_autojoin('#foo') not in ACKS


@patch('helga.plugins.operator.db')
def test_add_autojoin_adds(db):
    db.autojoin.find.return_value = db
    db.count.return_value = 0
    operator.add_autojoin('foo')
    db.autojoin.insert.assert_called_with({'channel': 'foo'})


@patch('helga.plugins.operator.db')
def test_remove_autojoin(db):
    operator.remove_autojoin('foo')
    db.autojoin.remove.assert_called_with({'channel': 'foo'})


@patch('helga.plugins.operator.db')
def test_join_autojoined_channels(db):
    client = Mock()
    db.autojoin.find.return_value = [
        {'channel': '#bots'},
        {'channel': u'☃'},
    ]
    operator.join_autojoined_channels(client)
    assert client.join.call_args_list == [call('#bots'), call(u'☃')]


@patch('helga.plugins.operator.registry')
def test_reload_plugin(plugins):
    plugins.reload.return_value = True
    assert "Successfully reloaded plugin 'foo'" == operator.reload_plugin('foo')

    plugins.reload.return_value = False
    assert "Failed to reload plugin 'foo'" == operator.reload_plugin('foo')


@patch('helga.plugins.operator.registry')
def test_reload_plugin_handles_unicode(plugins):
    snowman = u'☃'
    plugins.reload.return_value = True
    assert u"Successfully reloaded plugin '{0}'".format(snowman) == operator.reload_plugin(snowman)

    plugins.reload.return_value = False
    assert u"Failed to reload plugin '{0}'".format(snowman) == operator.reload_plugin(snowman)
