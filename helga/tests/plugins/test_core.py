from mock import Mock, patch
from unittest import TestCase

from helga.extensions.core import ControlExtension, HelpExtension
from helga.tests.util import mock_bot


class ControlExtensionTestCase(TestCase):

    def setUp(self):
        self.ctl = ControlExtension(Mock(), mock_bot())

    def test_handle_message_calls_extension_list(self):
        self.ctl.list_extensions = Mock()
        self.ctl.handle_message({'extension': True, 'list': True}, Mock())
        assert self.ctl.list_extensions.called

    def test_handle_message_calls_extension_disable(self):
        self.ctl.disable_extension = Mock()
        self.ctl.handle_message({'extension': True, 'disable': True, '<ext>': 'foo'}, Mock())
        assert self.ctl.disable_extension.called

    def test_list_extensions_enabled(self):
        self.ctl.registry.get_enabled.return_value = set(['foo'])

        assert self.ctl.list_extensions('bar', type='enabled') == 'Enabled extensions on bar: foo'

    def test_list_extensions_disabled(self):
        self.ctl.registry.get_disabled.return_value = set(['foo'])

        assert self.ctl.list_extensions('bar', type='disabled') == 'Disabled extensions on bar: foo'

    def test_list_extensions(self):
        # Test that we get both
        self.ctl.registry.get_enabled.return_value = set(['foo'])
        self.ctl.registry.get_disabled.return_value = set(['baz'])

        ret = self.ctl.list_extensions('bar')
        assert ret == ['Enabled extensions on bar: foo', 'Disabled extensions on bar: baz']

    def test_list_extensions_all_for_unknown_type(self):
        # Test that we get both
        self.ctl.registry.get_enabled.return_value = set(['foo'])
        self.ctl.registry.get_disabled.return_value = set(['baz'])

        ret = self.ctl.list_extensions('bar', type='foobar')
        assert ret == ['Enabled extensions on bar: foo', 'Disabled extensions on bar: baz']

    @patch('helga.extensions.core.db')
    def test_disable_extension_disables(self, db):
        self.ctl.registry.disable.return_value = True

        assert self.ctl.disable_extension('foo', 'bar') in self.ctl.acks

    @patch('helga.extensions.core.db')
    def test_disable_extension_invalid_ext_name(self, db):
        self.ctl.registry.disable.return_value = False

        assert self.ctl.disable_extension('foo', 'bar') not in self.ctl.acks

    @patch('helga.extensions.core.db')
    def test_enable_extension_disables(self, db):
        self.ctl.registry.disable.return_value = True

        assert self.ctl.disable_extension('foo', 'bar') in self.ctl.acks

    @patch('helga.extensions.core.db')
    def test_enable_extension_invalid_ext_name(self, db):
        self.ctl.registry.enable.return_value = False

        assert self.ctl.enable_extension('foo', 'bar') not in self.ctl.acks


class HelpExtensionTestCase(TestCase):

    def setUp(self):
        self.help = HelpExtension(Mock(), mock_bot())

    def test_help_all_single_extension(self):
        fake_ext = Mock(NAME='blah', usage='foo bar baz')
        self.help.registry.get_all_extensions.return_value = [fake_ext]

        assert 'blah: foo bar baz' in self.help.help_all()

    def test_help_all_multiple_extensions(self):
        fake_ext = Mock(NAME='blah', usage='foo bar baz')
        fake_ext2 = Mock(NAME='myext', usage='helga do something')
        self.help.registry.get_all_extensions.return_value = [fake_ext, fake_ext2]

        assert 'blah: foo bar baz' in self.help.help_all()
        assert 'myext: helga do something' in self.help.help_all()

    def test_help_unknown_ext(self):
        self.help.registry.get_all_extensions.return_value = [Mock()]

        assert "don't know that one" in self.help.help('foo')

    def test_help_misconfigured_ext(self):
        self.help.registry.is_extension_name.return_value = True
        self.help.registry.get_all_extensions.return_value = [Mock()]

        assert "don't know that one" in self.help.help('foo')

    def test_help_responds(self):
        fake_ext = Mock(NAME='blah', usage='foo bar baz')
        self.help.registry.is_extension_name.return_value = True
        self.help.registry.get_all_extensions.return_value = [fake_ext]

        assert 'USAGE: foo bar baz' == self.help.help('blah')
