from mock import Mock, patch
from unittest2 import TestCase

from helga import settings
from helga.extensions.jira import JiraExtension


_helga = Mock()
_helga.nick = 'helga'

settings.DISABLE_AUTOBOT = True


class JiraExtensionTestCase(TestCase):

    def setUp(self):
        self.jira = JiraExtension(load=False)
        settings.JIRA_URL = 'http://example.com/%(ticket)s'

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_public_matches(self):
        ret = self.jira.get_ticket_re('foo', 'helga jira foo bar', True)
        assert ret == 'bar'

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_public_no_match(self):
        ret = self.jira.get_ticket_re('baz', 'helga jira foo bar', True)
        assert ret is None

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_private_matches_with_nick(self):
        ret = self.jira.get_ticket_re('foo', 'helga jira foo bar', False)
        assert ret == 'bar'

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_private_matches_no_nick(self):
        ret = self.jira.get_ticket_re('foo', 'jira foo bar', False)
        assert ret == 'bar'

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_private_no_match_with_nick(self):
        ret = self.jira.get_ticket_re('baz', 'helga jira foo bar', False)
        assert ret is None

    @patch('helga.extensions.jira.helga', _helga)
    def test_get_ticket_re_private_no_match_no_nick(self):
        ret = self.jira.get_ticket_re('baz', 'jira foo bar', False)
        assert ret is None

    def patch_get_ticket_re(self, return_val):
        self.jira.get_ticket_re = Mock()
        self.jira.get_ticket_re.return_value = return_val

    @patch('helga.extensions.jira.helga', _helga)
    @patch('helga.extensions.jira.db')
    def test_handle_add_inserts_new_record(self, db):
        self.patch_get_ticket_re('foo')

        db.jira.find.return_value = db
        db.count.return_value = 0

        self.jira.handle_add('foo', True)

        assert 'foo' in self.jira.jira_pats
        assert db.jira.insert.called

    @patch('helga.extensions.jira.helga', _helga)
    @patch('helga.extensions.jira.db')
    def test_handle_add_has_existing_record_in_db(self, db):
        self.patch_get_ticket_re('foo')

        db.jira.find.return_value = db
        db.count.return_value = 1

        self.jira.handle_add('foo', True)

        assert 'foo' in self.jira.jira_pats
        assert not db.jira.insert.called

    @patch('helga.extensions.jira.helga', _helga)
    @patch('helga.extensions.jira.db')
    def test_handle_add_returns_none(self, db):
        self.patch_get_ticket_re(None)
        assert self.jira.handle_add('foo', True) is None

    @patch('helga.extensions.jira.helga', _helga)
    def test_handle_add_does_nothing_important(self):
        self.patch_get_ticket_re('foo')
        self.jira.jira_pats = ('foo',)

        assert self.jira.handle_add('foo', True)

    @patch('helga.extensions.jira.helga', _helga)
    @patch('helga.extensions.jira.db')
    def test_handle_remove_does_removing(self, db):
        self.patch_get_ticket_re('foo')
        self.jira.handle_remove('foo', True)
        assert db.jira.remove.called

    @patch('helga.extensions.jira.helga', _helga)
    def test_handle_remove_does_nothing(self):
        self.patch_get_ticket_re(None)
        assert self.jira.handle_remove('foo', True) is None

    @patch('helga.extensions.jira.helga', _helga)
    @patch('helga.extensions.jira.db')
    def test_handle_remove_removes_ticket(self, db):
        self.patch_get_ticket_re('foo')
        self.jira.jira_pats = set(['foo'])

        self.jira.handle_remove('foo', True)

        assert db.jira.remove.called
        assert 'foo' not in self.jira.jira_pats

    def test_contextualize_no_patterns(self):
        assert self.jira.contextualize('foo') is None

    def test_contextualize_no_pattern_match(self):
        self.jira.jira_pats = ('foobar',)
        assert self.jira.contextualize('barfoo-123') is None

    def test_contextualize_responds_with_url(self):
        self.jira.jira_pats = ('foobar',)
        ret = self.jira.contextualize('my message is foobar-123')

        assert 'http://example.com/foobar-123' in ret

    def test_contextualize_responds_many_urls(self):
        self.jira.jira_pats = ('foobar',)
        ret = self.jira.contextualize('look at foobar-123 and foobar-42')

        assert 'http://example.com/foobar-123' in ret
        assert 'http://example.com/foobar-42' in ret

    def test_contextualize_responds_many_url_patterns(self):
        self.jira.jira_pats = ('foobar', 'bazqux')
        ret = self.jira.contextualize('look at foobar-123 and bazqux-10')

        assert 'http://example.com/foobar-123' in ret
        assert 'http://example.com/bazqux-10' in ret

    def patch_for_dispatch(self):
        self.jira.handle_add = Mock()
        self.jira.handle_remove = Mock()
        self.jira.contextualize = Mock()

        self.jira.handle_add.return_value = None
        self.jira.handle_remove.return_value = None
        self.jira.contextualize.return_value = None

    def test_dispatch_responds_to_add(self):
        self.patch_for_dispatch()
        self.jira.handle_add.return_value = 'foo'

        ret = self.jira.dispatch('sducnan', '#all', 'check this', False)

        assert ret == 'foo'
        assert self.jira.handle_add.called
        assert not self.jira.handle_remove.called
        assert not self.jira.contextualize.called

    def test_dispatch_responds_to_remove(self):
        self.patch_for_dispatch()
        self.jira.handle_remove.return_value = 'foo'

        ret = self.jira.dispatch('sducnan', '#all', 'check this', False)

        assert ret == 'foo'
        assert self.jira.handle_add.called
        assert self.jira.handle_remove.called
        assert not self.jira.contextualize.called

    def test_dispatch_responds_to_contextualize(self):
        self.patch_for_dispatch()
        self.jira.contextualize.return_value = 'foo'

        ret = self.jira.dispatch('sducnan', '#all', 'check this', False)

        assert ret == 'foo'
        assert self.jira.handle_add.called
        assert self.jira.handle_remove.called
        assert self.jira.contextualize.called
