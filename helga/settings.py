import os
import sys
import warnings

SERVER = {
    'HOST': '192.168.55.101',
    'PORT': 6667,
}

LOG_LEVEL = 'DEBUG'

DEFAULT_NICK = 'helga'
CHANNELS = (
    ('#bots',),
)

AUTO_RECONNECT = True
RATE_LIMIT = None

OPERATORS = ('sduncan',)

MONGODB = {
    'HOST': 'localhost',
    'PORT': 27017,
    'DB': 'helga',
}


# Modules and their settings
EXTENSIONS = (
    'operator',
    'reviewboard',
    'jira',
    'facts',
    'haiku',
    'tanka',
    'loljava',
    'oneliner',
    'no_more_olga',
    'stfu',
    'dubstep',
    'icanhazascii',
    'mts',
    'wiki_whois',
    'fredoism',
    'giphy',
)

JIRA_URL = 'https://jira.cmgdigital.com/browse/%(ticket)s'
WIKI_URL = 'http://intranet.cmgdigital.com/display/~%(user)s/Home'
REVIEWBOARD_URL = 'http://reviews.ddtc.cmgdigital.com/r/%(review)s'

ALLOW_NICK_CHANGE = False


if 'HELGA_SETTINGS' in os.environ:
    try:
        path = os.environ['HELGA_SETTINGS']
        overrides = __import__(path, {}, {}, [path.split('.')[-1]])
    except ImportError:
        warnings.warn('Unabled to import HELGA_SETTINGS override. Is it on the path?')
    else:
        this = sys.modules[__name__]
        for attr in filter(lambda x: not x.startswith('_'), dir(overrides)):
            setattr(this, attr, getattr(overrides, attr))
