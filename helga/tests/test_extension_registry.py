from mock import Mock
from unittest import TestCase

from helga.extensions import ExtensionRegistry
from helga.tests.util import mock_bot


class ExtensionRegistryTestCase(TestCase):

    def setUp(self):
        self.registry = ExtensionRegistry(mock_bot(), load=False)

    def test_make_import_args_with_dots(self):
        ret = self.registry._make_import_args('foo.bar.baz')
        assert ret[0] == 'foo.bar.baz'
        assert ret[-1] == ['baz']

    def test_make_import_args_without_dots(self):
        ret = self.registry._make_import_args('foo')
        assert ret[0] == 'foo'
        assert ret[-1] == ['foo']

    def test_get_possible_extensions(self):
        class FakeModule(object):
            def __ignored(self):
                pass

            def not_ignored(self):
                pass

            def _also_not_ignored(self):
                pass

        fake = FakeModule()
        ret = self.registry._get_possible_extensions(fake)

        assert '__ignored' not in ret
        assert 'not_ignored' in ret
        assert '_also_not_ignored' in ret

    def test_get_enabled(self):
        self.registry.extension_names = set(['foo', 'bar', 'baz'])
        self.registry.disabled_extensions = {'#bots': set(['foo'])}

        enabled = self.registry.get_enabled('#bots')

        assert 'foo' not in enabled
        assert 'bar' in enabled
        assert 'baz' in enabled

    def test_get_disabled(self):
        self.registry.extension_names = set(['foo', 'bar', 'baz'])
        self.registry.disabled_extensions = {'#bots': set(['foo'])}

        disabled = self.registry.get_disabled('#bots')

        assert 'foo' in disabled

    def test_disable_unknown_extension_name(self):
        self.registry.disabled_extensions = {}
        self.registry.extension_names = set()

        assert not self.registry.disable('foo', '#bots')

    def test_disable(self):
        self.registry.disabled_extensions = {}
        self.registry.extension_names = set(['foo'])

        assert self.registry.disable('foo', '#bots')

    def test_is_disabled_for_class(self):
        class Fake(object):
            NAME = 'foo'

        self.registry.disabled_extensions = {'#bots': set(['foo'])}
        self.registry.extension_names = set(['foo'])

        assert self.registry.is_disabled(Fake, '#bots')

    def test_is_disabled_for_object(self):
        self.registry.disabled_extensions = {'#bots': set(['foo'])}
        self.registry.extension_names = set(['foo'])

        assert self.registry.is_disabled(Mock(NAME='foo'), '#bots')

    def test_is_disabled(self):
        self.registry.disabled_extensions = {'#bots': set(['foo'])}
        self.registry.extension_names = set(['foo'])

        assert self.registry.is_disabled('foo', '#bots')
