from mock import Mock, patch
from unittest import TestCase

from helga.extensions.haiku import HaikuExtension
from helga.tests.util import mock_bot


class HaikuExtensionTestCase(TestCase):

    def setUp(self):
        self.haiku = HaikuExtension(mock_bot())

    @patch('helga.extensions.haiku.db')
    def test_add(self, db):
        self.haiku.add(5, 'foobar')

        assert db.haiku.insert.called

    @patch('helga.extensions.haiku.db')
    def test_remove(self, db):
        self.haiku.remove(5, 'foobar')

        assert db.haiku.remove.called

    @patch('helga.extensions.haiku.db')
    def test_get_random_line(self, db):

        # We mock out the find, because we will do sorting and slicing
        def fake_find(q_dict):
            result = Mock()
            result.sort = result
            result.count.return_value = 1
            result.limit.return_value = result
            result.skip.return_value = result
            result.next.return_value = {'message': 'fives1'}

            return result

        db.haiku.find = fake_find
        line = self.haiku.get_random_line(5)

        assert line == 'fives1'

    @patch('helga.extensions.haiku.db')
    def test_get_random_line_returns_none(self, db):
        db.haiku.find.return_value = db
        db.count.return_value = 0

        assert self.haiku.get_random_line(5) is None

    def test_use_fives(self):
        self.haiku.add = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['one', 'two', 'three']

        poem = self.haiku.use(5, 'foo')

        assert 'foo' in (poem[0], poem[2])

    def test_use_fives_does_not_duplicate(self):
        self.haiku.add = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['foo', 'two', 'three']

        poem = self.haiku.use(5, 'foo')

        assert poem[0] == 'foo'
        assert poem[2] != 'foo'

    def test_use_sevens(self):
        self.haiku.add = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['one', 'two', 'three']

        poem = self.haiku.use(7, 'foo')

        assert poem[1] == 'foo'
