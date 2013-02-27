import tweepy

from helga import settings
from helga.log import setup_logger


logger = setup_logger(__name__)


def get_settings():
    return {
        'consumer_key': getattr(settings, 'TWITTER_CONSUMER_KEY', None),
        'consumer_secret': getattr(settings, 'TWITTER_CONSUMER_SECRET', None),
        'oauth_token': getattr(settings, 'TWITTER_OAUTH_TOKEN', None),
        'oauth_token_secret': getattr(settings, 'TWITTER_OAUTH_TOKEN_SECRET', None)
    }


def is_properly_configured(config):
    return all(config.values())


def message_140(message):
    max = 140

    if len(message) > max:
        logger.warning('Message exceeds %d characters. Truncating' % max)
        message = message[:max]

    return message


def get_api(config):
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['oauth_token'], config['oauth_token_secret'])
    api = tweepy.API(auth)

    return api


def tweet(message):
    config = get_settings()

    if not is_properly_configured(config):
        logger.warning('Twitter API requires consumer key, consumer secret, oauth token, oauth secret')
        return

    message = message_140(message)

    try:
        logger.info('Tweeting: %s' % message)
        status = get_api(config).update_status(message)
    except:
        logger.exception('Could not post status')
    else:
        tweet_url = 'http://twitter.com/%s/status/%s' % (getattr(settings, 'TWITTER_USERNAME', ''), status.id)
        logger.info('Tweeted: %s' % tweet_url)
        return tweet_url
