import tweepy

from helga import log, settings


logger = log.getLogger(__name__)


def is_properly_configured():
    return all([
        getattr(settings, 'TWITTER_CONSUMER_KEY', None),
        getattr(settings, 'TWITTER_CONSUMER_SECRET', None),
        getattr(settings, 'TWITTER_OAUTH_TOKEN', None),
        getattr(settings, 'TWITTER_OAUTH_TOKEN_SECRET', None),
    ])


def message_max(message, max):
    if len(message) > max:
        logger.warning('Message exceeds {0} characters. Truncating'.format(max))
        message = message[:max]
    return message


def message_140(message):
    return message_max(message, 140)


def get_api():
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(settings.TWITTER_OAUTH_TOKEN, settings.TWITTER_OAUTH_TOKEN_SECRET)
    return tweepy.API(auth)


def tweet(message):
    if not is_properly_configured():
        logger.error('Twitter API requires consumer key, consumer secret, oauth token, oauth secret')
        return

    message = message_140(message)

    try:
        logger.info('Tweeting: {0}'.format(message))
        status = get_api().update_status(message)
    except:
        logger.exception('Could not post status')
    else:
        tweet_url = 'http://twitter.com/{0}/status/{1}'.format(settings.TWITTER_USERNAME, status.id)
        logger.info('Tweeted: {0}'.format(tweet_url))
        return tweet_url
