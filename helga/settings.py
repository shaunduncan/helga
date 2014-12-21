import os
import sys

SERVER = {
    'HOST': 'localhost',
    'PORT': 6667,
}

LOG_LEVEL = 'DEBUG'

# Helga plugin priority values
PLUGIN_PRIORITY_LOW = 25
PLUGIN_PRIORITY_NORMAL = 50
PLUGIN_PRIORITY_HIGH = 75

# Control the behavior of argument parsing for command plugins
# By default this is a naive str.split(' '), however a plugin
# may need this behavior to be a bit more robust. By setting this value
# to True, shlex.split() will be used instead so that commands
# like `helga foo bar "baz qux"` will yield an argument list like
# ['bar', 'baz qux'] instead of ['bar', '"baz', 'qux"']. Shlex splits
# will be the default and only supported behavior in a future version.
COMMAND_ARGS_SHLEX = False

# Channel logging. Set CHANNEL_LOGGING_DIR
CHANNEL_LOGGING = False
CHANNEL_LOGGING_DIR = '.logs'
CHANNEL_LOGGING_HIDE_CHANNELS = []

NICK = 'helga'
CHANNELS = [
    ('#bots',),
]

AUTO_RECONNECT = True
AUTO_RECONNECT_DELAY = 5
RATE_LIMIT = None

OPERATORS = ['sduncan']

# MongoDB settings
DATABASE = {
    'HOST': 'localhost',
    'PORT': 27017,
    'DB': 'helga',
}

TIMEZONE = 'US/Eastern'

# The default set of plugins enabled on any channel.
# By default, potentially noisy plugins are disabled
ENABLED_PLUGINS = [
    'dubstep',
    'facts',
    'help',
    'jira',
    'loljava',
    'manager',
    'meant_to_say',
    'oneliner',
    'operator',
    'poems',
    'reminders',
    'reviewboard',
    'stfu',
    'webhooks',
    'wiki_whois',

    # Sometimes, giphy may give back a gif of questionable content
    # 'giphy',

    # These can get super annoying in public channels
    # 'icanhazascii',

    # Generally, olga isn't being used
    # 'no_more_olga',
]

# A list of webhook names that should be enabled on process startup.
# If this value is None, then all webhooks loaded via entry points
# are run. An empty list will not load any webhooks
ENABLED_WEBHOOKS = None

# Set to False if all responses returned by plugins should be returned
# over IRC. If True, the first responding plugin will send a response
PLUGIN_FIRST_RESPONDER_ONLY = True

# If set to True, a command can be run by asking directly.
# For example `helga foo`
COMMAND_PREFIX_BOTNICK = True

# If non-empty, this char can be used to invoke a command without
# requiring the bot's nick. For example `helga foo` could be run with
# `!foo` instead
COMMAND_PREFIX_CHAR = '!'

# MISC PLUGIN SETTINGS
FACTS_REQUIRE_NICKNAME = False

# Jira settings. If JIRA_SHOW_FULL_DESCRIPTION is false, only links to the Jira
# ticket will be shown. Otherwise, the ticket title will be pulled and shown.
# Full descriptions require JIRA_REST_API to be set.
# JIRA_USERNAME and JIRA_PASSWORD are optional if authentication is required
JIRA_URL = 'http://localhost/{ticket}'
JIRA_REST_API = ''
JIRA_SHOW_FULL_DESCRIPTION = False
JIRA_AUTH = ('', '')

REVIEWBOARD_URL = 'http://localhost/{review}'
WIKI_URL = 'http://localhost/{user}'

# WEBHOOKS SETTINGS
WEBHOOKS_PORT = 8080
WEBHOOKS_CREDENTIALS = []  # Tuples of (user, pass)


def configure(overrides):
    """
    Applies custom configuration to global helga settings. Overrides can either be
    a python import path string like 'foo.bar.baz' or a filesystem path like
    'foo/bar/baz.py'
    """
    this = sys.modules[__name__]

    # Filesystem path to settings file
    if os.path.isfile(overrides):
        execfile(overrides, this.__dict__)
        return

    # Module import path settings file
    fromlist = [overrides.split('.')[-1]]
    overrides = __import__(overrides, this.__dict__, {}, fromlist)

    for attr in filter(lambda x: not x.startswith('_'), dir(overrides)):
        setattr(this, attr, getattr(overrides, attr))
