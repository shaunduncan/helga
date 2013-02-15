from mock import Mock
from unittest import TestCase

from helga.extensions import ExtensionRegistry
from helga.extensions.base import HelgaExtension
from helga.tests.util import mock_bot


class ExtensionRegistryTestCase(TestCase):

    def setUp(self):
        self.registry = ExtensionRegistry(mock_bot(), load=False)

    def test_make_import_args(self):
        ret = self.registry._make_import_args('foo.bar.baz')
        assert ret[0] == 'foo.bar.baz'
        assert ret[-1] == ['baz']

    def test_load_module_members_adds_subclass(self):
        class MyClass(HelgaExtension):
            pass

        fake_module = Mock()
        fake_module.MyClass = MyClass

        self.registry._get_possible_extensions = Mock(return_value=['MyClass'])
        self.registry.load_module_members(fake_module)

        assert len(self.registry.ext) == 1
        assert isinstance(self.registry.ext.pop(), MyClass)

    def test_dispatch_returns_none(self):
        assert self.registry.dispatch('foo', 'bar', 'baz', True) is None

    def mock_extension(self, retval):
        ext = Mock()
        ext.dispatch.return_value = retval
        return ext

    def test_dispatch_returns_a_message(self):
        mock_ext = self.mock_extension('foo')
        self.registry.ext = [mock_ext]

        assert self.registry.dispatch('foo', 'bar', 'baz', True) == 'foo'

    def test_dispatch_returns_first_message(self):
        ext1 = self.mock_extension(None)
        ext2 = self.mock_extension('foo')
        ext3 = self.mock_extension('bar')

        self.registry.ext = [ext1, ext2, ext3]

        assert self.registry.dispatch('foo', 'bar', 'baz', True) == 'foo'
        assert ext1.dispatch.called
        assert ext2.dispatch.called
        assert not ext3.dispatch.called

    def test_get_possible_extensions(self):
        class TestModule(object):
            def __dir__(self):
                return ['foo', '__bar__', '_baz', 'qux__']
    
        ret = self.registry._get_possible_extensions(TestModule())

        assert len(ret) == 3
        assert '__bar__' not in ret
