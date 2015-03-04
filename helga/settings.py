"""
Default settings and configuration utilities
"""
import os
import sys

#: Dictionary of connection details. At a minimum this should contain keys
#: ``HOST`` and ``PORT`` which default to 'localhost' and 6667 respectively for irc.
#: Optionally, you can specify a boolean key ``SSL`` if you require helga to
#: connect via SSL. You may also specify keys ``USERNAME`` and ``PASSWORD``
#: if your server requires authentication. For example::
#:
#:     SERVER = {
#:         'HOST': 'localhost',
#:         'PORT': 6667,
#:         'SSL': False,
#:         'USERNAME': 'user',
#:         'PASSWORD': 'pass',
#:     }
#:
#: Additional, optional keys are supported for different chat backends:
#:
#: - ``TYPE``: the backend type to use, 'irc' or 'xmpp'
#: - ``MUC_HOST``: the MUC group chat domain like 'conference.example.com' for group chat
#: - ``JID``: A full jabber ID to use instead of USERNAME (xmpp only)
SERVER = {
    'HOST': 'localhost',
    'PORT': 6667,
    'TYPE': 'irc',
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

#: The preferred nick of the bot instance. For XMPP clients, this will be used when joining rooms.
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
#:
#: For XMPP/HipChat support, channel names should either be the full room JID in the form
#: of ``room@host`` or a simple channel name prefixed with a '#' such as ``#room``. Depending
#: on the configuration, the room JID will be constructed using the ``MUC_HOST`` value of the
#: ``SERVER`` setting or by prefixing 'conference.' to the ``HOST`` value.
CHANNELS = [
    ('#bots',),
]

#: A boolean indicating if the bot automatically reconnect on connection lost
AUTO_RECONNECT = True

#: An integer for the time, in seconds, to delay between reconnect attempts
AUTO_RECONNECT_DELAY = 5

#: IRC Only. An integer indicating the rate limit, in seconds, for messages sent over IRC.
#: This may help to prevent flood, but may degrade the performance of the bot, as it applies
#: to every message sent to IRC.
RATE_LIMIT = None

#: A list of chat nicks that should be considered operators/administrators
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

#: A list of plugin names that should be loaded by the plugin manager. This effectively serves
#: as a mechanism for explicitly including plugins that have been installed on the system.
#: If this value is True, the plugin manager will load any plugin configured with an entry
#: point and make it available for use. If it is None, or an empty list, no plugins will be loaded.
#: See :ref:`plugins` for more information.
ENABLED_PLUGINS = True

#: A list of plugin names that should NOT be loaded by the plugin manager. This effectively serves
#: as a mechanism for explicitly excluding plugins that have been installed on the system.
#: If this value is True, the plugin manager will NOT load any plugin configured with an entry
#: point. If it is None, or an empty list, no plugins will be blacklisted.
#: See :ref:`plugins` for more information.
DISABLED_PLUGINS = []

#: A list of plugin names that should be enabled automatically for any channel. If this value
#: is True, all plugins installed will be enabled by default. If this value is None, or an empty
#: list, no plugins will be enabled on channels by default. See :ref:`plugins` for more information.
DEFAULT_CHANNEL_PLUGINS = True

#: A list of whitelisted webhook names that should be loaded and enabled on process startup. If this value
#: is True, then all webhooks available are loaded and made available. An empty list or None implies
#: that no webhooks will be made available. See :ref:`webhooks` for more details.
ENABLED_WEBHOOKS = True

#: A list of blacklisted webhook names that should NOT be loaded and enabled on process startup. If this value
#: is True, then all webhooks available are loaded and made available. An empty list or None implies
#: that no webhooks will be made available. See :ref:`webhooks` for more details.
DISABLED_WEBHOOKS = None

#: A boolean, if True, the first response received from a plugin will be the only message
#: sent back to the chat server. If False, all responses are sent.
PLUGIN_FIRST_RESPONDER_ONLY = True

#: If a boolean and True, command plugins can be run by asking directly, such as 'helga foo_command'.
#: This can also be a string for specifically setting a nick type prefix (such as @NickName for HipChat)
COMMAND_PREFIX_BOTNICK = True

#: A string char, if non-empty, that can be used to invoke a command without requiring the bot's nick.
#: For example 'helga foo' could be run with '!foo'.
COMMAND_PREFIX_CHAR = '!'

#: A boolean that controls the behavior of argument parsing for command plugins. If False,
#: command plugin arguments are parsed using a naive whitespace split. If True, they will
#: be parsed using `shlex.split`. See :ref:`plugins.creating.commands` for more information.
#: The default is False, but this shlex parsing will be the only supported means of argument
#: string parsing in a future version.
COMMAND_ARGS_SHLEX = False

#: A boolean on whether commands should be treated with case insensitivity. For example,
#: a command 'foo' will respond to 'FOO', 'Foo', 'foo', etc.
COMMAND_IGNORECASE = False

#: The integer port the webhooks plugin should listen for http requests.
WEBHOOKS_PORT = 8080

#: List of two-tuple username and passwords used for http webhook basic authentication
WEBHOOKS_CREDENTIALS = []  # Tuples of (user, pass)


def configure(overrides):
    """
    Applies custom configuration to global helga settings. Overrides can either be
    a python import path string like 'foo.bar.baz' or a filesystem path like
    'foo/bar/baz.py'

    :param overrides: an importable python path string like 'foo.bar' or a filesystem path
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
