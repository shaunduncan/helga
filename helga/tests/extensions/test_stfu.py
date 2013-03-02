from mock import Mock
from unittest import TestCase

from helga.extensions.stfu import STFUExtension
from helga.tests.util import mock_bot


class STFUExtensionTestCase(TestCase):

    def setUp(self):
        self.stfu = STFUExtension(mock_bot())

    def test_is_silenced(self):
        self.stfu.silence('foo')
        assert self.stfu.is_silenced('foo')

    def test_is_silenced_not_silenced(self):
        self.stfu.unsilence('foo')
        assert not self.stfu.is_silenced('foo')

    def test_preprocess_no_action(self):
        msg = Mock(message='foo', channel='bar', response=None)
        self.stfu.preprocess(msg)
        assert msg.response is None

    def test_preprocess_responds_with_snark(self):
        msg = Mock(message='stfu', channel='bar', is_public=False, response=None)
        self.stfu.preprocess(msg)
        assert msg.response in self.stfu.snarks

    def test_preprocess_silences_channel(self):
        assert not self.stfu.is_silenced('bar')
        msg = Mock(message='helga stfu', channel='bar', is_public=True, response=None)
        self.stfu.preprocess(msg)
        assert self.stfu.is_silenced('bar')

    def test_preprocess_silences_channel_responds_once(self):
        msg = Mock(message='helga stfu', channel='bar', is_public=True, response=None)
        self.stfu.preprocess(msg)
        assert msg.response

        msg = Mock(message='helga stfu', channel='bar', is_public=True, response=None)
        self.stfu.preprocess(msg)
        assert not msg.response

    def test_preprocess_unsilences_channel(self):
        msg = Mock(message='helga speak', channel='bar', is_public=True, response=None)
        self.stfu.silence('bar')
        self.stfu.preprocess(msg)
        assert not self.stfu.is_silenced('bar')

    def test_preprocess_unsilences_channel_responds_once(self):
        self.stfu.silence('bar')

        msg = Mock(message='helga speak', channel='bar', is_public=True, response=None)
        self.stfu.preprocess(msg)
        assert msg.response

        msg = Mock(message='helga speak', channel='bar', is_public=True, response=None)
        self.stfu.preprocess(msg)
        assert not msg.response
