SERVER = {
    'HOST': '192.168.55.101',
    'PORT': 6667,
}

LOG_FILE = '/dev/stdout'
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
    'helga.extensions.jira',
    'helga.extensions.facts',
)

JIRA_URL = 'https://jira.cmgdigital.com/browse/%(ticket)s'
