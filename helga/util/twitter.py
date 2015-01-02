"""
Utilities for interacting with twitter

.. note::

    This module may be deprecated in the future
"""
import tweepy

from helga import log, settings


logger = log.getLogger(__name__)


def is_properly_configured():
    """
    Ensures that all necessary settings for communicating with twitter are configured.
    This includes:

    * ``TWITTER_CONSUMER_KEY``
    * ``TWITTER_CONSUMER_SECRET``
    * ``TWITTER_OAUTH_TOKEN``
    * ``TWITTER_OAUTH_TOKEN_SECRET``

    :returns: boolean, True if all settings are set
    """
    return all([
        getattr(settings, 'TWITTER_CONSUMER_KEY', None),
        getattr(settings, 'TWITTER_CONSUMER_SECRET', None),
        getattr(settings, 'TWITTER_OAUTH_TOKEN', None),
        getattr(settings, 'TWITTER_OAUTH_TOKEN_SECRET', None),
    ])


def message_max(message, max):
    """
    Returns a given message with a maximum length. Primarily used for additional logging

    :param str message: a message intended to send to twitter
    :param int max: the maximum length of the message
    :returns: the message truncated to a maximum length
    """
    if len(message) > max:
        logger.warning('Message exceeds %s characters. Truncating', max)
        message = message[:max]
    return message


def message_140(message):
    """
    A wrapper for message_max using 140 as a hard limit

    :param str message: a message intended to send to twitter
    :returns: the message truncated to a maximum length of 140 characters
    """
    return message_max(message, 140)


def get_api():
    """
    Constructs a ``tweepy.API`` object using configured twitter settings in ``helga.settings``.

    :returns: an instance of ``tweepy.API``
    """
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(settings.TWITTER_OAUTH_TOKEN, settings.TWITTER_OAUTH_TOKEN_SECRET)
    return tweepy.API(auth)


def tweet(message):
    """
    Sends a tweet using ``tweepy``. Ensures that helga is properly configured for accessing
    twitter and sends a message with a maximum character length of 140 characters.

    :param str message: the message to tweet
    :returns: a URL string of the posted tweet
    """
    if not is_properly_configured():
        logger.error('Twitter API requires consumer key, consumer secret, oauth token, oauth secret')
        return

    message = message_140(message)

    try:
        logger.info('Tweeting: %s', message)
        status = get_api().update_status(message)
    except:  # pragma: no cover
        logger.exception('Could not post status')
    else:
        tweet_url = 'http://twitter.com/{0}/status/{1}'.format(settings.TWITTER_USERNAME, status.id)
        logger.info('Tweeted: %s', tweet_url)
        return tweet_url
