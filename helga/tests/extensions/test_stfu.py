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

    def test_pre_dispatch_no_action(self):
        assert self.stfu.pre_dispatch('foo', 'bar', 'baz', True) == (None, 'baz')

    def test_pre_dispatch_responds_with_snark(self):
        ret = self.stfu.pre_dispatch('foo', 'bar', 'stfu', False)
        assert ret[0] in self.stfu.snarks

    def test_pre_dispatch_silences_channel(self):
        assert not self.stfu.is_silenced('bar')
        self.stfu.pre_dispatch('foo', 'bar', 'helga stfu', True)
        assert self.stfu.is_silenced('bar')

    def test_pre_dispatch_silences_channel_responds_once(self):
        ret1 = self.stfu.pre_dispatch('foo', 'bar', 'helga stfu', True)
        ret2 = self.stfu.pre_dispatch('foo', 'bar', 'helga stfu', True)

        assert ret1[0] in self.stfu.silence_acks
        assert ret2[0] is None

    def test_pre_dispatch_unsilences_channel(self):
        self.stfu.silence('bar')
        self.stfu.pre_dispatch('foo', 'bar', 'helga speak', True)
        assert not self.stfu.is_silenced('bar')

    def test_pre_dispatch_unsilences_channel_responds_once(self):
        self.stfu.silence('bar')

        ret1 = self.stfu.pre_dispatch('foo', 'bar', 'helga speak', True)
        ret2 = self.stfu.pre_dispatch('foo', 'bar', 'helga speak', True)

        assert ret1[0] in self.stfu.unsilence_acks
        assert ret2[0] is None
