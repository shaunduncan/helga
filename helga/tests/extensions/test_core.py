from mock import Mock
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

    def test_list_extensions(self):
        self.ctl.registry.enabled_extensions.return_value = set(['foo'])

        assert self.ctl.list_extensions('bar') == 'Extensions on this channel: foo'

    def test_disable_extension_disables(self):
        self.ctl.registry.disable_extension.return_value = True

        assert self.ctl.disable_extension('foo', 'bar') in self.ctl.acks

    def test_disable_extension_invalid_ext_name(self):
        self.ctl.registry.disable_extension.return_value = False

        assert self.ctl.disable_extension('foo', 'bar') not in self.ctl.acks


class HelpExtensionTestCase(TestCase):

    def setUp(self):
        self.help = HelpExtension(Mock(), mock_bot())

    def test_help_all_single_extension(self):
        fake_ext = Mock(NAME='blah', usage='foo bar baz')
        self.help.registry.get_commands.return_value = [fake_ext]

        assert 'blah usage: foo bar baz' in self.help.help_all()

    def test_help_all_multiple_extensions(self):
        fake_ext = Mock(NAME='blah', usage='foo bar baz')
        fake_ext2 = Mock(NAME='myext', usage='helga do something')
        self.help.registry.get_commands.return_value = [fake_ext, fake_ext2]

        assert 'blah usage: foo bar baz' in self.help.help_all()
        assert 'myext usage: helga do something' in self.help.help_all()

    def test_help_unknown_ext(self):
        self.help.registry.is_extension_name.return_value = False

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
