from mock import Mock, patch
from unittest import TestCase

from helga.extensions.haiku import HaikuExtension
from helga.tests.util import mock_bot


class HaikuExtensionTestCase(TestCase):

    def setUp(self):
        self.haiku = HaikuExtension(mock_bot())

    @patch('helga.extensions.haiku.db')
    def test_add_line(self, db):
        self.haiku.add_line(5, 'foobar')

        assert db.haiku.insert.called

    @patch('helga.extensions.haiku.db')
    def test_make_poem(self, db):

        # We mock out the find, because we will do sorting and slicing
        def fake_find(q_dict):
            result = Mock()
            result.sort = result
            result.count.return_value = 3

            if q_dict.get('syllables', 5) == 5:
                result.return_value = [
                    {'message': 'fives1'},
                    {'message': 'fives2'},
                    {'message': 'fives3'}
                ]
            else:
                result.return_value = [
                    {'message': 'sevens1'},
                    {'message': 'sevens2'},
                    {'message': 'sevens3'}
                ]

            return result

        db.haiku.find = fake_find
        poem = self.haiku.make_poem()

        assert len(poem) == 3
        assert poem[0].startswith('fives')
        assert poem[1].startswith('sevens')
        assert poem[2].startswith('fives')

    @patch('helga.extensions.haiku.db')
    def test_make_poem_returns_none(self, db):
        db.haiku.find.return_value = db
        db.count.return_value = 0

        assert self.haiku.make_poem() is None

    def test_add_use_line_fives(self):
        self.haiku.add_line = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['one', 'two', 'three']

        poem = self.haiku.add_use_line(5, 'foo')

        assert 'foo' in (poem[0], poem[2])

    def test_add_use_line_fives_does_not_duplicate(self):
        self.haiku.add_line = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['foo', 'two', 'three']

        poem = self.haiku.add_use_line(5, 'foo')

        assert poem[0] == 'foo'
        assert poem[2] != 'foo'

    def test_add_use_line_sevens(self):
        self.haiku.add_line = Mock()
        self.haiku.make_poem = Mock()
        self.haiku.make_poem.return_value = ['one', 'two', 'three']

        poem = self.haiku.add_use_line(7, 'foo')

        assert poem[1] == 'foo'

    def test_parse_message_is_public_raises_without_nick(self):
        self.assertRaises(Exception,
                          self.haiku.parse_message,
                          'haiku add fives this is a haiku',
                          True)

    def test_parse_message_is_public_parses_with_nick(self):
        retval = self.haiku.parse_message('helga haiku add fives this is a haiku', True)
        assert ('add', 'fives', 'this is a haiku') == retval

    def test_parse_message_not_public_optional_nick(self):
        retval = self.haiku.parse_message('haiku add fives this is a haiku', False)
        assert ('add', 'fives', 'this is a haiku') == retval
