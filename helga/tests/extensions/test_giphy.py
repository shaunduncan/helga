from unittest import TestCase

from giphypop import GiphyApiException
from mock import Mock, patch
from pretend import stub

from helga.extensions.giphy import GiphyExtension
from helga.tests.util import mock_bot


class GiphyExtensionTestCase(TestCase):

    def setUp(self):
        self.g = GiphyExtension(mock_bot())
        self.g.api = Mock()
        self.img = stub(media_url='GIF')

    def test_gifme_returns_random_gif(self):
        self.g.api.random_gif.return_value = self.img

        resp = self.g.gifme()
        assert self.g.api.random_gif.called
        assert resp == self.img.media_url

    def test_gifme_returns_translated(self):
        self.g.api.random_gif.side_effect = GiphyApiException
        self.g.api.translate.return_value = self.img

        resp = self.g.gifme(search='foo')
        assert self.g.api.translate.called
        assert resp == self.img.media_url

    def test_gifme_returns_searched(self):
        self.g.api.random_gif.side_effect = GiphyApiException
        self.g.api.translate.side_effect = GiphyApiException
        self.g.api.search_list.return_value = [self.img]

        resp = self.g.gifme(search='foo')
        assert self.g.api.search_list.called
        assert resp == self.img.media_url

    def test_gifme_returns_snark(self):
        self.g.api.random_gif.side_effect = GiphyApiException
        self.g.api.translate.side_effect = GiphyApiException
        self.g.api.search_list.side_effect = GiphyApiException

        assert self.g.gifme(search='foo') in self.g.sad_panda
