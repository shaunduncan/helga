import time

from mock import Mock, patch
from unittest import TestCase

from helga import settings
from helga.extensions.facts import FactExtension
from helga.tests.util import mock_bot


class FactExtensionTestCase(TestCase):

    def setUp(self):
        self.facts = FactExtension(mock_bot())

    def test_add_fact_no_match(self):
        assert self.facts.add_fact('foobar') is None

    def patch_db_count(self, db, count_val):
        db.facts.find.return_value = db
        db.count.return_value = count_val

    @patch('helga.extensions.facts.db')
    def test_add_fact_adds_db_record(self, db):
        self.patch_db_count(db, 0)
        self.facts.add_fact('foo is bar', 'me') is None

        assert db.facts.insert.called

    @patch('helga.extensions.facts.db')
    def test_add_fact_adds_db_record_with_reply(self, db):
        self.patch_db_count(db, 0)
        self.facts.add_fact('foo is <reply> bar', 'me') is None

        db.facts.insert.assertCalledWith({
            'term': 'foo',
            'fact': 'bar'
        })

    @patch('helga.extensions.facts.db')
    def test_add_fact_exising_record(self, db):
        self.patch_db_count(db, 1)
        assert not db.facts.insert.called

    def test_remove_fact_no_match(self):
        assert self.facts.remove_fact('foobar', True) is None

    def test_remove_fact_no_nick_match(self):
        assert self.facts.remove_fact('you forget that', True) is None

    @patch('helga.extensions.facts.db')
    def test_remove_fact_removes_when_is_public(self, db):
        self.facts.remove_fact('helga forget foo', True)
        db.facts.remove.assertCalledWith({'term': 'foo'})

    @patch('helga.extensions.facts.db')
    def test_remove_fact_removes_when_private_no_nick(self, db):
        self.facts.remove_fact('forget foo', False)
        db.facts.remove.assertCalledWith({'term': 'foo'})

    def test_show_fact_no_match(self):
        assert self.facts.show_fact('well ok then?') is None

    @patch('helga.extensions.facts.db')
    def test_show_fact_not_in_db(self, db):
        db.facts.find_one.return_value = None
        assert self.facts.show_fact('foo?') is None
        assert db.facts.find_one.called

    @patch('helga.extensions.facts.db')
    def test_show_fact_gets_db_record_no_set_time(self, db):
        db.facts.find_one.return_value = {
            'term': 'foo',
            'fact': 'foo is bar',
            'set_by': 'nobody'
        }

        ret = self.facts.show_fact('foo?')

        assert ret == 'foo is bar (nobody)'

    @patch('helga.extensions.facts.db')
    def test_show_fact_gets_db_record_with_set_time(self, db):
        db.facts.find_one.return_value = {
            'term': 'foo',
            'fact': 'foo is bar',
            'set_by': 'nobody',
            'set_date': 1360849874.686594,  # 02/14/2013 08:51AM
        }

        ret = self.facts.show_fact('foo?')

        assert ret == 'foo is bar (nobody on 02/14/2013 08:51AM)'

    def test_dispatch_no_reponse(self):
        assert self.facts.dispatch('foo', 'bar', 'baz', True) is None

    def patch_dispatch_calls(self, add_ret, rem_ret, show_ret):
        self.facts.add_fact = Mock(return_value=add_ret)
        self.facts.remove_fact = Mock(return_value=rem_ret)
        self.facts.show_fact = Mock(return_value=show_ret)

    def test_dispatch_is_add_response(self):
        self.patch_dispatch_calls('foo', None, None)

        assert self.facts.dispatch('foo', 'bar', 'baz', True) == 'foo'
        assert self.facts.add_fact.called

    def test_dispatch_is_remove_response(self):
        self.patch_dispatch_calls(None, 'foo', None)

        assert self.facts.dispatch('foo', 'bar', 'baz', True) == 'foo'
        assert self.facts.remove_fact.called

    def test_dispatch_is_show_response(self):
        self.patch_dispatch_calls(None, None, 'foo')

        assert self.facts.dispatch('foo', 'bar', 'baz', True) == 'foo'
        assert self.facts.show_fact.called
