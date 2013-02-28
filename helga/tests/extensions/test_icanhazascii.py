import time

from unittest import TestCase

from helga.extensions.icanhazascii import ICanHazAsciiExtension
from helga.tests.util import mock_bot


class ICanHazAsciiExtensionTestCase(TestCase):

    def setUp(self):
        self.ascii = ICanHazAsciiExtension(mock_bot())

    def test_is_flooded(self):
        self.ascii.last_used = {'foo': time.time()}
        assert self.ascii.is_flooded('foo')

    def test_is_flooded_not_recorded(self):
        self.ascii.last_used = {}
        assert not self.ascii.is_flooded('foo')

    def test_is_flooded_not_flooded(self):
        self.ascii.last_used = {'foo': time.time() - 86400}
        assert not self.ascii.is_flooded('foo')
