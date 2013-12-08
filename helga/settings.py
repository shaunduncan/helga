import os
import sys
import warnings

SERVER = {
    'HOST': '192.168.55.101',
    'PORT': 6667,
}

LOG_LEVEL = 'DEBUG'

NICK = 'helga'
CHANNELS = [
    ('#bots',),
]

AUTO_RECONNECT = True
RATE_LIMIT = None

OPERATORS = ['sduncan']

# MongoDB settings
DATABASE = {
    'HOST': 'localhost',
    'PORT': 27017,
    'DB': 'helga',
}

TIMEZONE = 'US/Eastern'

# Plugin settings
FACTS_REQUIRE_NICKNAME = False
JIRA_URL = 'http://localhost/{ticket}'
REVIEWBOARD_URL = 'http://localhost/{review}'


if 'HELGA_SETTINGS' in os.environ:
    try:
        path = os.environ['HELGA_SETTINGS']
        overrides = __import__(path, {}, {}, [path.split('.')[-1]])
    except ImportError:
        warnings.warn('Unabled to import HELGA_SETTINGS override. Is it on sys.path?')
    else:
        this = sys.modules[__name__]
        for attr in filter(lambda x: not x.startswith('_'), dir(overrides)):
            setattr(this, attr, getattr(overrides, attr))
