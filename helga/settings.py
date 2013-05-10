import os
import sys
import warnings

SERVER = {
    'HOST': '192.168.55.101',
    'PORT': 6667,
}

LOG_LEVEL = 'DEBUG'

DEFAULT_NICK = 'helga'
CHANNELS = ('#bots',)

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
    'helga.extensions.operator',
    'helga.extensions.reviewboard',
    'helga.extensions.jira',
    'helga.extensions.facts',
    'helga.extensions.haiku',
    'helga.extensions.tanka',
    'helga.extensions.loljava',
    'helga.extensions.oneliner',
    'helga.extensions.no_more_olga',
    'helga.extensions.stfu',
    'helga.extensions.dubstep',
    'helga.extensions.icanhazascii',
    'helga.extensions.mts',
)

JIRA_URL = 'https://jira.cmgdigital.com/browse/%(ticket)s'
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
