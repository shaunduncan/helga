from mock import Mock, patch
from unittest import TestCase

from helga.extensions.tanka import TankaExtension
from helga.tests.util import mock_bot


class TankaExtensionTestCase(TestCase):

    def setUp(self):
        self.tanka = TankaExtension(mock_bot())

    @patch('helga.extensions.haiku.db')
    def test_add_line(self, db):
        self.tanka.add_line(5, 'foobar')

        assert db.haiku.insert.called

    @patch('helga.extensions.haiku.db')
    @patch('helga.extensions.tanka.db')
    def test_make_poem(self, t_db, h_db):

        # We mock out the find, because we will do sorting and slicing
        def fake_find(q_dict):
            result = Mock()
            result.sort = result
            result.count.return_value = 3

            if q_dict.get('syllables', 5) == 5:
                result.return_value = ['fives1', 'fives2', 'fives3']
            else:
                result.return_value = ['sevens1', 'sevens2', 'sevens3']

            return result

        h_db.haiku.find = fake_find
        t_db.haiku.find = fake_find
        poem = self.tanka.make_poem()

        assert len(poem) == 5
        assert poem[0].startswith('fives')
        assert poem[1].startswith('sevens')
        assert poem[2].startswith('fives')
        assert poem[3].startswith('sevens')
        assert poem[4].startswith('sevens')

    @patch('helga.extensions.haiku.db')
    @patch('helga.extensions.tanka.db')
    def test_make_poem_returns_none(self, t_db, h_db):
        h_db.haiku.find.return_value = h_db
        h_db.count.return_value = 0

        t_db.haiku.find.return_value = t_db
        t_db.count.return_value = 0

        assert self.tanka.make_poem() is None
