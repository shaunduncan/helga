from mock import Mock
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

    def test_find_all_matches(self):
        self.oneliner.responses = {'foo': 'bar'}
        assert self.oneliner.find_all_matches(Mock(message='foo'))

    def test_process_sets_response(self):
        msg = Mock(message='foo', response=None)
        self.oneliner.find_all_matches = Mock(return_value = ['bar'])
        self.oneliner.process(msg)

        assert msg.response == 'bar'

    def test_process_supports_multiple_options(self):
        msg = Mock(message='foo', response=None)
        self.oneliner.find_all_matches = Mock(return_value = [('foo', 'bar')])
        self.oneliner.process(msg)

        assert msg.response in ('foo', 'bar')
