from mock import patch
from pretend import stub

from helga.plugins import jira


settings_stub = stub(JIRA_URL='http://example.com/{ticket}',
                     JIRA_SHOW_FULL_DESCRIPTION=False)


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
