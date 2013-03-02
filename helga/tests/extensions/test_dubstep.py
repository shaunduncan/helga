import time

from unittest import TestCase

from helga.extensions.dubstep import DubstepExtension
from helga.tests.util import mock_bot


class DubstepExtensionTestCase(TestCase):

    def setUp(self):
        self.dubstep = DubstepExtension(mock_bot())

    def test_transform_match_does_wubs(self):
        assert 'wubwub' in self.dubstep.transform_match('foo')

    def test_transform_match_stops_after_max(self):
        self.dubstep.last_wub = time.time()
        self.dubstep.max_wubs = 3

        assert 'wubwub' in self.dubstep.transform_match('foo')
        assert 'wubwub' in self.dubstep.transform_match('foo')
        assert 'wubwub' in self.dubstep.transform_match('foo')
        assert 'STOP' in self.dubstep.transform_match('foo')
        assert 'wubwub' in self.dubstep.transform_match('foo')
