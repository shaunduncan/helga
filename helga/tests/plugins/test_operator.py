from mock import Mock, patch
from pretend import stub

from helga.plugins import operator, ACKS


def test_operator_ignores_non_oper_user():
    client = stub(operators=['me'])
    assert operator.operator(client, '#bots', 'sduncan', 'do something', '', '') in operator.nopes


def test_operator_join_calls_client_join():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['join', '#foo'])
    client.join.assertCalledWith('#foo')


def test_operator_join_ignores_invalid_channel():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['join', 'foo'])
    assert not client.join.called


def test_operator_leave_calls_client_leave():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['leave', '#foo'])
    client.leave.assertCalledWith('#foo')


def test_operator_leave_ignores_invalid_channel():
    client = Mock(operators=['me'])
    operator.operator(client, '#bots', 'me', 'do something', 'op', ['leave', 'foo'])
    assert not client.leave.called


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
    db.autojoin.insert.assertCalledWith({'channel': 'foo'})


@patch('helga.plugins.operator.db')
def test_remove_autojoin(db):
    operator.remove_autojoin('foo')
    db.autojoin.remove.assertCalledWith({'channel': 'foo'})
