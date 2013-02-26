from mock import patch
from unittest import TestCase

from helga.extensions.reviewboard import ReviewboardExtension
from helga.tests.util import mock_bot


class ReviewboardExtensionTestCase(TestCase):

    def setUp(self):
        self.rb = ReviewboardExtension(mock_bot())

    def test_contextualize_no_match(self):
        assert self.rb.contextualize('foo') is None

    @patch('helga.extensions.reviewboard.settings')
    def test_contextualize_responds_with_url(self, settings):
        settings.REVIEWBOARD_URL = 'http://example.com/%(review)s'
        resp = self.rb.contextualize('this is cr123')
        assert 'http://example.com/123' in resp

    @patch('helga.extensions.reviewboard.settings')
    def test_contextualize_responds_with_many_urls(self, settings):
        settings.REVIEWBOARD_URL = 'http://example.com/%(review)s'
        resp = self.rb.contextualize('this is cr123 and cr42')
        assert 'http://example.com/123' in resp
        assert 'http://example.com/42' in resp
