from mock import Mock, patch
from unittest import TestCase

from helga import settings
from helga.extensions.jira import JiraExtension
from helga.tests.util import mock_bot


class JiraExtensionTestCase(TestCase):

    def setUp(self):
        self.jira = JiraExtension(mock_bot())
        settings.JIRA_URL = 'http://example.com/%(ticket)s'

    @patch('helga.extensions.jira.db')
    def test_add_re_inserts_new_record(self, db):
        db.jira.find.return_value = db
        db.count.return_value = 0

        self.jira.add_re('foo')

        assert 'foo' in self.jira.jira_pats
        assert db.jira.insert.called

    @patch('helga.extensions.jira.db')
    def test_add_re_has_existing_record_in_db(self, db):
        db.jira.find.return_value = db
        db.count.return_value = 1

        self.jira.add_re('foo')

        assert 'foo' in self.jira.jira_pats
        assert not db.jira.insert.called

    def test_add_re_does_nothing_important(self):
        self.jira.jira_pats = ('foo',)

        assert self.jira.add_re('foo')

    @patch('helga.extensions.jira.db')
    def test_remove_re_does_removing(self, db):
        self.jira.remove_re('foo')
        assert db.jira.remove.called

    @patch('helga.extensions.jira.db')
    def test_remove_re_removes_ticket(self, db):
        self.jira.jira_pats = set(['foo'])

        self.jira.remove_re('foo')

        assert db.jira.remove.called
        assert 'foo' not in self.jira.jira_pats

    def test_contextualize_no_patterns(self):
        msg = Mock(message='foo', response=None)
        self.jira.contextualize(msg)

        assert msg.response is None

    def test_contextualize_no_pattern_match(self):
        msg = Mock(message='barfoo-123', response=None)
        self.jira.jira_pats = ('foobar',)
        self.jira.contextualize(msg)

        assert msg.response is None

    def test_contextualize_responds_with_url(self):
        msg = Mock(message='my message is foobar-123', response=None)
        self.jira.jira_pats = ('foobar',)
        self.jira.contextualize(msg)

        assert 'http://example.com/foobar-123' in msg.response

    def test_contextualize_responds_many_urls(self):
        msg = Mock(message='look at foobar-123 and foobar-42', response=None)
        self.jira.jira_pats = ('foobar',)
        self.jira.contextualize(msg)

        assert 'http://example.com/foobar-123' in msg.response
        assert 'http://example.com/foobar-42' in msg.response

    def test_contextualize_responds_many_url_patterns(self):
        msg = Mock(message='look at foobar-123 and bazqux-10', response=None)
        self.jira.jira_pats = ('foobar', 'bazqux')
        self.jira.contextualize(msg)

        assert 'http://example.com/foobar-123' in msg.response
        assert 'http://example.com/bazqux-10' in msg.response

    def test_contextualize_ignores_urls(self):
        msg = Mock(message='look at http://foo.com/foobar-123', response=None)
        self.jira.jira_pats = ('foobar',)
        self.jira.contextualize(msg)

        assert msg.response is None
