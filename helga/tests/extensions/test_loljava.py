from unittest import TestCase

from helga.extensions.loljava import LOLJavaExtension
from helga.tests.util import mock_bot


class LOLJavaExtensionTestCase(TestCase):

    def setUp(self):
        self.loljava = LOLJavaExtension(mock_bot())

    def test_make_bullshit_java_thing(self):
        assert self.loljava.make_bullshit_java_thing()

    def test_dispatch_returns_message(self):
        assert self.loljava.dispatch('foo', 'bar', 'java', True)
        assert self.loljava.dispatch('foo', 'bar', 'lol java', True)
        assert self.loljava.dispatch('foo', 'bar', 'loljava, crazy', True)
        assert self.loljava.dispatch('foo', 'bar', '[JAVA]', True)

    def test_dispatch_returns_none(self):
        assert self.loljava.dispatch('foo', 'bar', 'php', True) is None
        assert self.loljava.dispatch('foo', 'bar', 'javascript', True) is None
