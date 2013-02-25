from unittest import TestCase

from helga.extensions.oneliner import OneLinerExtension
from helga.tests.util import mock_bot


class OneLinerExtensionTestCase(TestCase):

    def setUp(self):
        self.oneliner = OneLinerExtension(mock_bot())

    def test_decompose_response_no_nick_change(self):
        newnick, resp = self.oneliner.decompose_response('this is by itself')

        assert newnick is None
        assert resp == 'this is by itself'

    def test_decompose_response_nick_change(self):
        newnick, resp = self.oneliner.decompose_response('foobar:::this is a response')

        assert newnick == 'foobar'
        assert resp == 'this is a response'
