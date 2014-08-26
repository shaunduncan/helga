# -*- coding: utf8 -*-
from mock import Mock, patch

from helga import settings
from helga.util import twitter


def test_is_properly_configured():
    settings.TWITTER_CONSUMER_KEY = 'foo'
    settings.TWITTER_CONSUMER_SECRET = 'foo'
    settings.TWITTER_OAUTH_TOKEN = 'foo'
    settings.TWITTER_OAUTH_TOKEN_SECRET = 'foo'

    assert twitter.is_properly_configured()

    settings.TWITTER_CONSUMER_KEY = ''
    assert not twitter.is_properly_configured()

    delattr(settings, 'TWITTER_CONSUMER_KEY')
    assert not twitter.is_properly_configured()


def test_message_max():
    msg1 = 'a' * 255
    msg2 = 'a'
    assert len(twitter.message_max(msg1, 140)) == 140
    assert len(twitter.message_max(msg2, 140)) == 1


def test_message_max_handles_unicode():
    snowman1 = u'☃' * 255
    snowman2 = u'☃'
    assert len(twitter.message_max(snowman1, 140)) == 140
    assert len(twitter.message_max(snowman2, 140)) == 1


@patch('helga.util.twitter.get_api')
def test_tweet(api):
    settings.TWITTER_CONSUMER_KEY = 'foo'
    settings.TWITTER_CONSUMER_SECRET = 'foo'
    settings.TWITTER_OAUTH_TOKEN = 'foo'
    settings.TWITTER_OAUTH_TOKEN_SECRET = 'foo'
    settings.TWITTER_USERNAME = 'helgabot'

    api.return_value = api
    api.update_status.return_value = Mock(id=123456789)

    assert twitter.tweet('foo') == 'http://twitter.com/helgabot/status/123456789'


@patch('helga.util.twitter.get_api')
def test_tweet_handles_unicode(api):
    settings.TWITTER_CONSUMER_KEY = 'foo'
    settings.TWITTER_CONSUMER_SECRET = 'foo'
    settings.TWITTER_OAUTH_TOKEN = 'foo'
    settings.TWITTER_OAUTH_TOKEN_SECRET = 'foo'
    settings.TWITTER_USERNAME = 'helgabot'

    api.return_value = api
    api.update_status.return_value = Mock(id=123456789)

    assert twitter.tweet(u'☃') == 'http://twitter.com/helgabot/status/123456789'
