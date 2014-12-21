# -*- coding: utf -*-
import pytest

from mock import call, patch, Mock
from pretend import stub

from helga.plugins import jira, ResponseNotReady


settings_stub = stub(JIRA_URL='http://example.com/{ticket}',
                     JIRA_SHOW_FULL_DESCRIPTION=False,
                     JIRA_REST_API='http://example.com/api/{ticket}')


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.db')
def test_init_jira_patterns(mock_db):
    mock_db.jira.find.return_value = [{'re': 'foo'}]
    jira.JIRA_PATTERNS.clear()

    assert 'foo' not in jira.JIRA_PATTERNS
    jira.init_jira_patterns()
    assert 'foo' in jira.JIRA_PATTERNS


def test_find_jira_numbers_ignores_url():
    message = 'this has a url http://example.com/foobar-123'
    jira.JIRA_PATTERNS = set('foobar')
    assert jira.find_jira_numbers(message) == []


def test_find_jira_numbers_finds_all():
    message = 'this ia about foo-123, bar-456, baz-789, and qux-000'
    jira.JIRA_PATTERNS = set(['foo', 'bar', 'baz'])

    tickets = jira.find_jira_numbers(message)
    assert 'foo-123' in tickets
    assert 'bar-456' in tickets
    assert 'baz-789' in tickets


def test_find_jira_numbers_ignores_unknown():
    message = 'this ia about foo-123, bar-456, baz-789, and qux-000'
    jira.JIRA_PATTERNS = set(['foo', 'bar', 'baz'])

    tickets = jira.find_jira_numbers(message)
    assert 'quz-000' not in tickets


@patch('helga.plugins.jira.db')
def test_add_re_inserts_new_record(db):
    db.jira.find.return_value = db
    db.count.return_value = 0
    jira.JIRA_PATTERNS.clear()

    jira.add_re('foo')

    assert 'foo' in jira.JIRA_PATTERNS
    assert db.jira.insert.called


@patch('helga.plugins.jira.db')
def test_add_re_has_existing_record_in_db(db):
    db.jira.find.return_value = db
    db.count.return_value = 1
    jira.JIRA_PATTERNS.clear()

    jira.add_re('foo')

    assert 'foo' in jira.JIRA_PATTERNS
    assert not db.jira.insert.called


@patch('helga.plugins.jira.db')
def test_remove_re_does_removing(db):
    jira.remove_re('foo')
    assert db.jira.remove.called


@patch('helga.plugins.jira.db')
def test_remove_re_removes_ticket(db):
    jira.JIRA_PATTERNS = set(['foo'])
    jira.remove_re('foo')

    assert db.jira.remove.called
    assert 'foo' not in jira.JIRA_PATTERNS


@patch('helga.plugins.jira.settings', settings_stub)
def test_jira_match():
    expected = 'me might be talking about JIRA ticket: http://example.com/foo-123'
    assert expected == jira.jira_match(None, '#bots', 'me', 'this is about foo-123', ['foo-123'])


@patch('helga.plugins.jira.settings', settings_stub)
def test_jira_match_multiple():
    resp = jira.jira_match(None, '#bots', 'me', 'foo-123 and bar-456', ['foo-123', 'bar-456'])
    assert 'http://example.com/foo-123' in resp
    assert 'http://example.com/bar-456' in resp


@patch('helga.plugins.jira.settings', settings_stub)
def test_jira_match_handles_unicode():
    snowman = u'☃'
    expected = u'me might be talking about JIRA ticket: http://example.com/{0}'.format(snowman)
    response = jira.jira_match(None, '#bots', 'me', u'this is about {0}'.format(snowman), [snowman])
    assert response == expected


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.reactor')
def test_jira_match_does_async(reactor):
    client = Mock()
    settings_stub.JIRA_SHOW_FULL_DESCRIPTION = True
    urls = {'foo-123': 'http://example.com/foo-123'}
    expected_call = call(0, jira.jira_full_descriptions, client, '#bots', urls)
    with pytest.raises(ResponseNotReady):
        jira.jira_match(client, '#bots', 'me', 'ticket foo-123', ['foo-123'])
        assert reactor.callLater.call_args == expected_call


@patch('helga.plugins.jira.remove_re')
@patch('helga.plugins.jira.add_re')
def test_jira_command_ignores_invalid_format(add_re, remove_re):
    arg_tests = [
        [],
        ['foo'],
        [u'☃']
    ]

    for args in arg_tests:
        assert jira.jira_command(None, '#bots', 'me', 'foo', 'bar', args) is None
        assert not add_re.called
        assert not remove_re.called

        # Reset mocks
        add_re.reset_mock()
        remove_re.reset_mock()


@patch('helga.plugins.jira.remove_re')
@patch('helga.plugins.jira.add_re')
def test_jira_command_add_re(add_re, remove_re):
    jira.jira_command(None, '#bots', 'me', 'foo', 'bar', ['add_re', 'foobar'])
    assert add_re.called
    assert not remove_re.called


@patch('helga.plugins.jira.remove_re')
@patch('helga.plugins.jira.add_re')
def test_jira_command_remove_re(add_re, remove_re):
    jira.jira_command(None, '#bots', 'me', 'foo', 'bar', ['remove_re', 'foobar'])
    assert not add_re.called
    assert remove_re.called


@patch('helga.plugins.jira.remove_re')
@patch('helga.plugins.jira.add_re')
def test_jira_command_unknown(add_re, remove_re):
    jira.jira_command(None, '#bots', 'me', 'foo', 'bar', ['wat', 'foobar'])
    assert not add_re.called
    assert not remove_re.called


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.requests')
def test_rest_desc_request_error(requests):
    response = Mock()
    response.raise_for_status.side_effect = Exception
    requests.get.return_value = response
    assert jira._rest_desc('foo', 'url') is None


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.requests')
def test_rest_desc(requests):
    response = Mock()
    response.json.return_value = {
        'fields': {
            'summary': 'title',
        },
    }
    requests.get.return_value = response

    assert jira._rest_desc('foo', 'url') == '[FOO] title (url)'


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.requests')
def test_rest_desc_without_summary(requests):
    response = Mock()
    response.json.side_effect = Exception
    requests.get.return_value = response

    assert jira._rest_desc('foo', 'url') == '[FOO] url'


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.requests')
def test_rest_desc_handles_unicode(requests):
    snowman = u'☃'
    response = Mock()
    response.json.return_value = {
        'fields': {
            'summary': snowman,
        },
    }
    requests.get.return_value = response

    assert jira._rest_desc(snowman, snowman) == u'[{0}] {0} ({0})'.format(snowman)

    response.json.side_effect = Exception
    assert jira._rest_desc(snowman, snowman) == u'[{0}] {0}'.format(snowman)


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.HTTPBasicAuth')
@patch('helga.plugins.jira._rest_desc')
def test_jira_full_descriptions_handles_no_auth(rest_desc, auth):
    client = Mock()
    rest_desc.return_value = 'blah'
    settings_stub.JIRA_AUTH = ('', '')
    urls = {'foo': 'foo_url', 'bar': 'bar_url'}

    jira.jira_full_descriptions(client, '#bots', urls)

    assert not auth.called
    rest_desc.assert_has_calls([
        call('foo', 'foo_url', None),
        call('bar', 'bar_url', None),
    ], any_order=True)


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.HTTPBasicAuth')
@patch('helga.plugins.jira._rest_desc')
def test_jira_full_descriptions_handles_auth(rest_desc, auth):
    client = Mock()
    auth.return_value = auth
    rest_desc.return_value = 'blah'

    settings_stub.JIRA_AUTH = ('user', 'pass')
    urls = {'foo': 'foo_url', 'bar': 'bar_url'}

    jira.jira_full_descriptions(client, '#bots', urls)

    assert call('foo', 'foo_url', auth) in rest_desc.call_args_list
    assert call('bar', 'bar_url', auth) in rest_desc.call_args_list


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.HTTPBasicAuth')
@patch('helga.plugins.jira._rest_desc')
def test_jira_full_descriptions_handles_unicode(rest_desc, auth):
    snowman = u'☃'
    client = Mock()
    auth.return_value = auth
    rest_desc.return_value = snowman

    settings_stub.JIRA_AUTH = (snowman, snowman)
    urls = {snowman: u'{0}_url'.format(snowman)}

    jira.jira_full_descriptions(client, snowman, urls)

    assert rest_desc.call_args_list == [
        call(snowman, u'{0}_url'.format(snowman), auth),
    ]


@patch('helga.plugins.jira.jira_match')
@patch('helga.plugins.jira.jira_command')
def test_jira_plugin_handles_command(command, match):
    args = ['client', 'channel', 'nick', 'message', 'cmd', ['foo', 'bar', 'baz']]
    jira.jira(*args)
    assert command.called
    assert not match.called
    command.assert_called_with(*args)


@patch('helga.plugins.jira.jira_match')
@patch('helga.plugins.jira.jira_command')
def test_jira_plugin_handles_match(command, match):
    args = ['client', 'channel', 'nick', 'message', ['foo', 'bar', 'baz']]
    jira.jira(*args)
    assert not command.called
    assert match.called
    match.assert_called_with(*args)


def test_find_jira_numbers_with_no_patterns():
    with patch.object(jira, 'JIRA_PATTERNS', set()):
        assert [] == jira.find_jira_numbers('foo-123')


@patch('helga.plugins.jira.settings', settings_stub)
@patch('helga.plugins.jira.db')
def test_find_jira_numbers_when_no_patterns(mock_db):
    with patch.object(jira, 'JIRA_PATTERNS', set()):
        with patch.object(jira, 'jira_match'):
            jira.jira._plugins[1](Mock(), '#bots', 'me', 'foo-123')
            assert not jira.jira_match.called
