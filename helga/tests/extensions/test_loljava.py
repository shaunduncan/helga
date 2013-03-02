import re

from unittest import TestCase

from helga.extensions.loljava import LOLJavaExtension
from helga.tests.util import mock_bot


class LOLJavaExtensionTestCase(TestCase):

    def setUp(self):
        self.loljava = LOLJavaExtension(mock_bot())

    def test_make_bullshit_java_thing(self):
        assert self.loljava.make_bullshit_java_thing()

    def test_regex_matches_java(self):
        assert re.match(self.loljava.context, 'java')
        assert re.match(self.loljava.context, 'loljava')

    def test_regex_ignores_javascript(self):
        assert not re.match(self.loljava.context, 'javascript')
