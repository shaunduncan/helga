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

    def test_get_command(self):
        assert self.stfu.get_command('helga foo') == 'foo'

    def test_get_command_finds_nothing(self):
        assert self.stfu.get_command('helga, this is crap') is None

    def test_get_command_finds_nothing_when_nick_required(self):
        assert self.stfu.get_command('foo') is None

    def test_get_command_nick_not_required(self):
        assert self.stfu.get_command('foo', nick_required=False) == 'foo'

    def patch_get_command(self, retval):
        self.stfu.get_command = Mock()
        self.stfu.get_command.return_value = retval

    def test_pre_dispatch_no_action(self):
        self.patch_get_command(None)
        assert self.stfu.pre_dispatch('foo', 'bar', 'baz', True) is None

    def test_pre_dispatch_responds_with_snark(self):
        self.patch_get_command(self.stfu.STFU)
        ret = self.stfu.pre_dispatch('foo', 'bar', 'baz', False)
        assert ret in self.stfu.snarks

    def test_pre_dispatch_silences_channel(self):
        self.patch_get_command(self.stfu.STFU)

        assert not self.stfu.is_silenced('bar')
        self.stfu.pre_dispatch('foo', 'bar', 'baz', True)
        assert self.stfu.is_silenced('bar')

    def test_pre_dispatch_silences_channel_responds_once(self):
        self.patch_get_command(self.stfu.STFU)
        ret1 = self.stfu.pre_dispatch('foo', 'bar', 'baz', True)
        ret2 = self.stfu.pre_dispatch('foo', 'bar', 'baz', True)

        assert ret1 in self.stfu.silence_acks
        assert ret2 is None

    def test_pre_dispatch_unsilences_channel(self):
        self.patch_get_command(self.stfu.SPEAK)

        self.stfu.silence('bar')
        self.stfu.pre_dispatch('foo', 'bar', 'baz', True)
        assert not self.stfu.is_silenced('bar')

    def test_pre_dispatch_unsilences_channel_responds_once(self):
        self.patch_get_command(self.stfu.SPEAK)

        self.stfu.silence('bar')

        ret1 = self.stfu.pre_dispatch('foo', 'bar', 'baz', True)
        ret2 = self.stfu.pre_dispatch('foo', 'bar', 'baz', True)

        assert ret1 in self.stfu.unsilence_acks
        assert ret2 is None
