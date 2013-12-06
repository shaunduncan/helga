from mock import Mock, patch
from unittest import TestCase

from helga.extensions.tanka import TankaExtension
from helga.tests.util import mock_bot


class TankaExtensionTestCase(TestCase):

    def setUp(self):
        self.tanka = TankaExtension(mock_bot())

    @patch('helga.extensions.haiku.db')
    def test_add(self, db):
        self.tanka.add(5, 'foobar')

        assert db.haiku.insert.called

    def test_make_poem(self):

        # We mock out the find, because we will do sorting and slicing
        def fake_random_line(syllables, about=None, by=None):
            if syllables == 5:
                return 'fives'
            elif syllables == 7:
                return 'sevens'
            else:
                return ''

        self.tanka.get_random_line = fake_random_line
        poem = self.tanka.make_poem()

        assert len(poem) == 5
        assert poem == ['fives', 'sevens', 'fives', 'sevens', 'sevens']

    def test_make_poem_returns_none(self):
        self.tanka.get_random_line = Mock(return_value=None)

        assert self.tanka.make_poem() is None
