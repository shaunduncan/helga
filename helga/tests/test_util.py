from mock import patch, Mock
from unittest import TestCase

from helga.util.twitter import (is_properly_configured,
                                message_140,
                                tweet)


class TwitterTestCase(TestCase):

    def create_settings(self):
        return {
            'consumer_key': 'foo',
            'consumer_secret': 'foo',
            'oauth_token': 'foo',
            'oauth_token_secret': 'foo'
        }

    def test_message_140(self):
        assert message_140('foo bar baz') == 'foo bar baz'

    def test_message_140_truncates(self):
        assert len(message_140('a' * 150)) == 140

    def test_is_properly_configured(self):
        assert is_properly_configured(self.create_settings())

    def test_is_properly_configured_missing_data(self):
        config = self.create_settings()
        config['oauth_token'] = None

        assert not is_properly_configured(config)

    @patch('helga.util.twitter.get_api')
    @patch('helga.util.twitter.get_settings')
    def test_tweet_nothing_on_api_failure(self, get_settings, get_api):
        get_settings.return_value = self.create_settings()

        get_api.return_value = get_api
        get_api.side_effect = Exception

        assert tweet('foo') is None

    @patch('helga.util.twitter.settings')
    @patch('helga.util.twitter.get_api')
    @patch('helga.util.twitter.get_settings')
    def test_tweet_returns_status_url(self, get_settings, get_api, settings):
        settings.TWITTER_USERNAME = 'foobar'
        get_settings.return_value = self.create_settings()

        get_api.return_value = get_api
        get_api.update_status.return_value = Mock(id=12345)

        # we don't patch settings
        assert tweet('foo') == 'http://twitter.com/foobar/status/12345'
