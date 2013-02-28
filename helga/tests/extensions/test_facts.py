import time

from mock import Mock, patch
from unittest import TestCase

from helga import settings
from helga.extensions.facts import FactExtension
from helga.tests.util import mock_bot


class FactExtensionTestCase(TestCase):

    def setUp(self):
        self.facts = FactExtension(mock_bot())

    def patch_db_count(self, db, count_val):
        db.facts.find.return_value = db
        db.count.return_value = count_val

    @patch('helga.extensions.facts.db')
    def test_add_fact_adds_db_record(self, db):
        self.patch_db_count(db, 0)
        self.facts.add_fact('foo', 'me') is None

        assert db.facts.insert.called

    @patch('helga.extensions.facts.db')
    def test_add_fact_adds_db_record_adds_correct_data(self, db):
        self.patch_db_count(db, 0)
        self.facts.add_fact('foo', 'foo is bar') is None

        db.facts.insert.assertCalledWith({
            'term': 'foo',
            'fact': 'foo is bar'
        })

    @patch('helga.extensions.facts.db')
    def test_add_fact_exising_record(self, db):
        self.patch_db_count(db, 1)
        self.facts.add_fact('foo', 'bar')
        assert not db.facts.insert.called

    @patch('helga.extensions.facts.db')
    def test_remove_fact(self, db):
        assert self.facts.remove_fact('foo')

    def test_show_fact_no_match(self):
        assert self.facts.show_fact('well ok then?') is None

    @patch('helga.extensions.facts.db')
    def test_show_fact_not_in_db(self, db):
        db.facts.find_one.return_value = None
        assert self.facts.show_fact('foo') is None
        assert db.facts.find_one.called

    @patch('helga.extensions.facts.db')
    def test_show_fact_gets_db_record_no_set_time(self, db):
        db.facts.find_one.return_value = {
            'term': 'foo',
            'fact': 'foo is bar',
            'set_by': 'nobody'
        }

        ret = self.facts.show_fact('foo')

        assert ret == 'foo is bar (nobody)'

    @patch('helga.extensions.facts.db')
    def test_show_fact_gets_db_record_with_set_time(self, db):
        db.facts.find_one.return_value = {
            'term': 'foo',
            'fact': 'foo is bar',
            'set_by': 'nobody',
            'set_date': 1360849874.686594,  # 02/14/2013 08:51AM
        }

        ret = self.facts.show_fact('foo')

        assert ret == 'foo is bar (nobody on 02/14/2013 08:51AM)'
