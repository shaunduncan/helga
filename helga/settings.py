"""
Default settings and configuration utilities
"""
import os
import sys

#: Dictionary of IRC connection details. At a minimum this should contain keys
#: ``HOST`` and ``PORT`` which default to 'localhost' and 6667 respectively.
#: Optionally, you can specify a boolean key ``SSL`` if you require helga to
#: connect to IRC via SSL. You may also specify keys ``USERNAME`` and ``PASSWORD``
#: if your IRC server requires authentication. For example::
#:
#:     SERVER = {
#:         'HOST': 'localhost',
#:         'PORT': 6667,
#:         'SSL': False,
#:         'USERNAME': 'user',
#:         'PASSWORD': 'pass',
#:     }
SERVER = {
    'HOST': 'localhost',
    'PORT': 6667,
}


#: A string for the logging level helga should use for process logging
LOG_LEVEL = 'DEBUG'

#: A string, if set, a string indicating the log file for python logs. By default helga
#: will log directly to stdout
LOG_FILE = None

#: A string that is compatible with configuring a python logging formatter.
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s'

#: Integer value for 'low' priority plugins (see :ref:`plugins.priorities`)
PLUGIN_PRIORITY_LOW = 25

#: Integer value for 'normal' priority plugins (see :ref:`plugins.priorities`)
PLUGIN_PRIORITY_NORMAL = 50

#: Integer value for 'high' priority plugins (see :ref:`plugins.priorities`)
PLUGIN_PRIORITY_HIGH = 75

#: A boolean, if True, will enable conversation logging on all channels
CHANNEL_LOGGING = False

#: If :data:`CHANNEL_LOGGING` is enabled, this is a string of the directory to which channel logs
#: should be written.
CHANNEL_LOGGING_DIR = '.logs'

#: A list of channel names (either with or without a '#' prefix) that will be hidden in the
#: browsable channel log web ui.
CHANNEL_LOGGING_HIDE_CHANNELS = []

#: The preferred nick of the bot instance
NICK = 'helga'

#: A list of channels to automatically join. You can specify either a single channel name
#: or a two-tuple of channel name, and password. For example::
#:
#:     CHANNELS = [
#:         '#bots',
#:         ('#foo', 'password'),
#:     ]
#:
#: Note that this setting is only for hardcoded autojoined channels. Helga also responds
#: to /INVITE commands as well offers a builtin plugin to configure autojoin channels at
#: runtime (see :ref:`builtin.plugins.operator`)
CHANNELS = [
    ('#bots',),
]

#: A boolean indicating if the bot automatically reconnect on connection lost
AUTO_RECONNECT = True

#: An integer for the time, in seconds, to delay between reconnect attempts
AUTO_RECONNECT_DELAY = 5

#: An integer indicating the rate limit, in seconds, for messages sent over IRC. This may help
#: to prevent flood, but may degrade the performance of the bot, as it applies to every message
#: sent to IRC.
RATE_LIMIT = None

#: A list of IRC nicks that should be considered operators/administrators
OPERATORS = []

#: A dictionary containing connection info for MongoDB. The minimum settings that should
#: exist here are 'HOST', the MongoDB host, 'PORT, the MongoDB port, and 'DB' which should be the
#: MongoDB collection to use. These values default to 'localhost', 27017, and 'helga' respectively.
#: Both 'USERNAME' and 'PASSWORD' can be specified if MongoDB requires authentication. For example::
#:
#:     DATABASE = {
#:         'HOST': 'localhost',
#:         'PORT': 27017,
#:         'DB': 'helga',
#:         'USERNAME': 'foo',
#:         'PASSWORD': 'bar',
#:     }
DATABASE = {
    'HOST': 'localhost',
    'PORT': 27017,
    'DB': 'helga',
}

#: The default timezone for the bot instance
TIMEZONE = 'US/Eastern'

#: A list of plugin names that should be enabled automatically for any channel. Note that this
#: does not mean plugins that are loaded. By default, any plugin that has been installed will
#: be loaded and made available. This should be a list of the entry point names defined by each
#: plugin. See :ref:`plugins` for more information.
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

#: A list of webhook names that should be enabled on process startup. If this value is None,
#: then all webhooks available are loaded and made available. An empty list implies that no
#: webhooks will be made available. See :ref:`webhooks` for more details.
ENABLED_WEBHOOKS = None

#: A boolean, if True, the first response received from a plugin will be the only message
#: sent over IRC. If False, all responses are sent.
PLUGIN_FIRST_RESPONDER_ONLY = True

#: A boolean, if True, command plugins can be run by asking directly, such as 'helga foo_command'.
COMMAND_PREFIX_BOTNICK = True

#: A string char, if non-empty, that can be used to invoke a command without requiring the bot's nick.
#: For example 'helga foo' could be run with '!foo'.
COMMAND_PREFIX_CHAR = '!'

#: A boolean that controls the behavior of argument parsing for command plugins. If False,
#: command plugin arguments are parsed using a naive whitespace split. If True, they will
#: be parsed using :func:`shlex.split`. See :ref:`plugins.creating.commands` for more information.
#: The default is False, but this shlex parsing will be the only supported means of argument
#: string parsing in a future version.
COMMAND_ARGS_SHLEX = False

#: A boolean on whether commands should be treated with case insensitivity. For example,
#: a command 'foo' will respond to 'FOO', 'Foo', 'foo', etc.
COMMAND_IGNORECASE = False

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

#: The integer port the webhooks plugin should listen for http requests.
WEBHOOKS_PORT = 8080

#: List of two-tuple username and passwords used for http webhook basic authentication
WEBHOOKS_CREDENTIALS = []  # Tuples of (user, pass)


def configure(overrides):
    """
    Applies custom configuration to global helga settings. Overrides can either be
    a python import path string like 'foo.bar.baz' or a filesystem path like
    'foo/bar/baz.py'

    :param str overrides: an importable python path string like 'foo.bar' or a filesystem path
                          to a python file like 'foo/bar.py'
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
