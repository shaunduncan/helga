from mock import patch
from unittest import TestCase

from helga.extensions.reviewboard import ReviewboardExtension
from helga.tests.util import mock_bot


class ReviewboardExtensionTestCase(TestCase):

    def setUp(self):
        self.rb = ReviewboardExtension(mock_bot())

    @patch('helga.extensions.reviewboard.settings')
    def test_transform_match(self, settings):
        settings.REVIEWBOARD_URL = 'http://example.com/%(review)s'
        assert self.rb.transform_match('1234') == 'http://example.com/1234'
