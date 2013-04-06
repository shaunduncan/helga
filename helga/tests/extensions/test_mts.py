import re
from unittest import TestCase

from mock import Mock

from helga.extensions.mts import MTSExtension
from helga.tests.util import mock_bot


class MTSExtensionTestCase(TestCase):

    def setUp(self):
        self.mts = MTSExtension(mock_bot())
        self.message = Mock(message='foo', channel='bar', from_nick='me')

    def test_record_last(self):
        self.mts.record_last(self.message)

        assert self.mts.last['bar']['me'] == 'foo'

    def test_clear_last(self):
        self.mts.last['bar']['me'] = 'foo'
        self.mts.clear_last(self.message)

        assert self.mts.last['bar']['me'] == ''

    def test_get_last(self):
        self.mts.last['bar']['me'] = 'foo'

        assert self.mts.get_last(self.message) == 'foo'

    def test_contextualize_replaces_text(self):
        self.mts.record_last(self.message)
        next = Mock(message='s/foo/baz/', channel='bar', from_nick='me')
        self.mts.contextualize(next)

        assert 'meant to say: baz' in next.response

    def test_contextualize_ignores_if_no_last(self):
        next = Mock(message='s/foo/baz/', channel='bar', from_nick='me', response=None)
        self.mts.contextualize(next)

        assert next.response is None
