"""
Helga's core plugin library containing base implementations for creating plugins
as well as utilities for managing plugins at runtime
"""
from __future__ import absolute_import
import functools
import pkg_resources
import random
import re
import shlex
import sys
import warnings

from collections import defaultdict
from itertools import ifilter, imap
from operator import methodcaller

import smokesignal

from helga import log, settings
from helga.util.encodings import from_unicode, to_unicode


logger = log.getLogger(__name__)


#: A collection of pre-canned acknowledgement type responses
ACKS = [
    'roger',
    '10-4',
    'no problem',
    'will do',
    'you got it',
    'anything you say',
    'sure thing',
    'ok',
    'right-o',
    'consider it done',
]


#: The value for low priority plugins.
#: Configurable via setting :data:`~helga.settings.PLUGIN_PRIORITY_LOW`
PRIORITY_LOW = settings.PLUGIN_PRIORITY_LOW

#: The value for normal priority plugins.
#: Configurable via setting :data:`~helga.settings.PLUGIN_PRIORITY_NORMAL`
PRIORITY_NORMAL = settings.PLUGIN_PRIORITY_NORMAL

#: The value for high priority plugins.
#: Configurable via setting :data:`~helga.settings.PLUGIN_PRIORITY_HIGH`
PRIORITY_HIGH = settings.PLUGIN_PRIORITY_HIGH


if not settings.COMMAND_ARGS_SHLEX:
    warnings.warn(u'Command arg parsing will default to shlex in a future version', FutureWarning)


def random_ack():
    """
    Returns a random choice from :data:`ACKS`
    """
    return random.choice(ACKS)


class ResponseNotReady(Exception):
    """
    Exception raised by plugins that perform some async operation using
    twisted deferreds. If the bot is configured to only allow the first plugin
    response (by default), then any plugin raising this will prevent further
    plugin execution

    (see :ref:`plugins.async`)
    """


class Registry(object):
    """
    Simple plugin registry that handles dispatching messages to registered plugins.
    Plugins can be disabled or enabled per channel. By default, all plugins are loaded, but not
    enabled on a channel unless it exists in :data:`~helga.settings.DEFAULT_CHANNEL_PLUGINS`.
    This is done so that potentially annoying plugins can be enabled on-demand. Plugin loading
    can be limited to a whitelist via :data:`~helga.settings.ENABLED_PLUGINS` or restricted
    to a blacklist via :data:`~helga.settings.DISABLED_PLUGINS`.

    .. attribute:: plugins
        :annotation: = {}

        A dictionary mapping plugin names to decorated functions or :class:`Plugin` subclasses

    .. attribute:: enabled_plugins
        :annotation: = {}

        A dictionary of enabled plugin names per channel, keyed by channel name
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Only here so we only maintain one registry for the life of the application. There
        is some state-specific things that shouldn't be lost in the event the chat client
        loses the connection to the server
        """
        if cls.__instance is None:
            cls.__instance = super(Registry, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        if not hasattr(self, 'plugins'):
            self.plugins = {}

        self.plugin_names = set(ep.name for ep in pkg_resources.iter_entry_points('helga_plugins'))

        # Plugins whitelist/blacklist
        self.whitelist_plugins = self._create_plugin_list('ENABLED_PLUGINS', default=True)
        self.blacklist_plugins = self._create_plugin_list('DISABLED_PLUGINS', default=set())

        # Figure out default channel plugins using the whitelist and blacklist
        default = self._create_plugin_list('DEFAULT_CHANNEL_PLUGINS', default=set())

        # Make sure to exclude extras
        self.default_channel_plugins = (default & self.whitelist_plugins) - self.blacklist_plugins

        if not hasattr(self, 'enabled_plugins'):
            # Enabled plugins is a dict: channel -> set()
            self.enabled_plugins = defaultdict(lambda: self.default_channel_plugins)

        smokesignal.on('started', self.load)

    def _create_plugin_list(self, setting_name, default):
        """
        Used to get either plugin whitelists or blacklists

        :param setting_name: either ENABLED_PLUGINS or DISABLED_PLUGINS
        :param default: the default value to use if the setting does not exist
        """
        plugins = getattr(settings, setting_name, default)
        if isinstance(plugins, bool):
            return self.plugin_names if plugins else set()
        else:
            return set(plugins or [])

    def register(self, name, fn_or_cls):
        """
        Register a decorated plugin function or :class:`Plugin` subclass with a given name

        :param name: the name of the plugin
        :param fn_or_cls: a decorated plugin function or :class:`Plugin` subclass
        :raises: TypeError if the ``fn_or_cls`` argument is not a decorated plugin function or
                 :class:`Plugin` subclass
        """
        # Make sure we're working with an instance
        try:
            if issubclass(fn_or_cls, Plugin):
                fn_or_cls = fn_or_cls()
        except TypeError:
            pass

        if not (isinstance(fn_or_cls, Plugin) or hasattr(fn_or_cls, '_plugins')):
            raise TypeError(u"Plugin {0} must be a subclass of Plugin, or a decorated function".format(name))

        self.plugins[name] = fn_or_cls

    @property
    def all_plugins(self):
        """
        A set of all registered plugin names
        """
        return set(self.plugins.keys())

    def get_plugin(self, name):
        """
        Get a plugin by name

        :param name: the name of the plugin
        :returns: a plugin implementation (decorated function or :class:`Plugin` sublclass)
        """
        return self.plugins.get(name, None)

    def disable(self, channel, *plugins):
        """
        Disable a plugin or plugins on a desired channel

        :param channel: the desired chat channel
        :param \*plugins: a list of plugin names to disable
        """
        self.enabled_plugins[channel] = self.enabled_plugins[channel].difference(set(plugins))

    def enable(self, channel, *plugins):
        """
        Enable a plugin or plugins on a desired channel

        :param channel: the desired chat channel
        :param \*plugins: a list of plugin names to enable
        """
        self.enabled_plugins[channel] = self.enabled_plugins[channel].union(set(plugins))

    def load(self):
        """
        Load all plugins registered via setuptools entry point named ``helga_plugins`` and
        initialize them. For example::

            entry_points = {
                'helga_plugins': [
                    'plugin_name = mylib.mymodule:MyPluginClass',
                ],
            }

        Note that this loading honors plugin whitelists and blacklists from the settings
        :data:`~helga.settings.ENABLED_PLUGINS` and :data:`~helga.settings.DISABLED_PLUGINS`
        respectively. If there are no whitelisted plugins, nothing is loaded. If a plugin
        is in the blacklist, it is not loaded. If a plugin is not listed in the whitelist,
        it is not loaded.
        """
        if not self.whitelist_plugins:
            logger.warning('Plugin whitelist was empty, none, or false. Skipping.')
            smokesignal.emit('plugins_loaded')
            return

        for entry_point in pkg_resources.iter_entry_points(group='helga_plugins'):
            if entry_point.name in self.blacklist_plugins:
                logger.info('Skipping blacklisted plugin %s', entry_point.name)
                continue

            if entry_point.name not in self.whitelist_plugins:
                logger.info('Skipping non-whitelisted plugin %s', entry_point.name)
                continue

            try:
                logger.info('Loading and registering plugin %s', entry_point.name)
                self.register(entry_point.name, entry_point.load())
            except:
                logger.exception('Error initializing plugin %s', entry_point)

        smokesignal.emit('plugins_loaded')

    def reload(self, name):
        """
        Reloads a plugin with a given name. This is equivalent to finding the registered
        entry point module and using the python builtin ``reload()``.

        :param name: the desired plugin to reload
        :returns: True if reloaded, False if an exception occurred
        """
        if name not in self.plugins:
            # FIXME: This should raise
            return u"Unknown plugin '{0}'. Is it installed?".format(name)

        for entry_point in pkg_resources.iter_entry_points(group='helga_plugins'):
            if entry_point.name != name:
                continue

            # FIXME: exceptions should bubble up
            try:
                reload(sys.modules[entry_point.module_name])
                self.register(entry_point.name, entry_point.load())
                return True
            except:
                logger.exception('Failed to reload plugin %s', entry_point)
                return False

    def prioritized(self, channel, high_to_low=True):
        """
        Obtain a list of enabled plugins for a given channel ordered according to their priority
        (see :ref:`plugins.priorities`). The default action is to return a list ordered from most
        important to least important.

        :param channel: the chat channel for the enabled plugin list
        :param high_to_low: priority ordering, True for most important to least important.
        """
        plugins = []
        for name in self.enabled_plugins[channel]:
            if name not in self.plugins:
                logger.debug('Plugin %s may not be installed or have incorrect entry_point information', name)
                continue

            # Decorated functions will have this
            if hasattr(self.plugins[name], '_plugins'):
                plugins.extend(self.plugins[name]._plugins)
            else:
                plugins.append(self.plugins[name])

        return sorted(plugins, key=lambda p: getattr(p, 'priority', PRIORITY_NORMAL), reverse=high_to_low)

    def preprocess(self, client, channel, nick, message):
        """
        Invoke the ``preprocess`` method for each plugin on a given channel according to plugin priority.
        Any exceptions from plugins will be suppressed and logged.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: the channel from which the message came
        :param nick: the nick of the user sending the message
        :param message: the original message received
        :returns: a three-tuple (channel, nick, message) containing modifications all preprocessor
                  plugins have made
        """
        for plugin in self.prioritized(channel):
            try:
                channel, nick, message = plugin.preprocess(client, channel, nick, message)
            except:
                logger.exception('Calling preprocess on plugin %s failed', plugin)
                continue

        return channel, nick, message

    def process(self, client, channel, nick, message):
        """
        Invoke the ``process`` method for each plugin on a given channel according to plugin priority.
        Any exceptions from plugins will be suppressed and logged. All return values from plugin
        ``process`` methods are collected unless the setting
        :data:`~helga.settings.PLUGIN_FIRST_RESPONDER_ONLY` is set to True or a plugin raises
        :exc:`~helga.plugins.ResponseNotReady`, in which case the first plugin to return a response or raise
        :exc:`~helga.plugins.ResponseNotReady` will prevent others from processing. All response strings are
        explicitly converted to unicode.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: the channel from which the message came
        :param nick: the nick of the user sending the message
        :param message: the original message received
        :returns: a list of non-empty unicode response strings
        """
        responses = []
        first_responder = getattr(settings, 'PLUGIN_FIRST_RESPONDER_ONLY', False)

        for plugin in self.prioritized(channel):
            try:
                resp = plugin.process(client, channel, nick, message)
            except ResponseNotReady:
                if first_responder:
                    break
                continue  # pragma: no cover Python == 2.7
            except:
                logger.exception('Calling process on plugin %s failed', plugin)
                continue

            if not resp:
                continue

            # Chained decorator style plugins return a list of strings
            if isinstance(resp, (tuple, list)):
                # Be sure to filter Nones, then strip
                responses.extend(imap(lambda s: (s or '').strip(), resp))
            else:
                responses.append(resp.strip())

            if responses and first_responder:
                break

        # FIXME: Explicit conversion to unicode might not make sense. Perpahs
        # a warning should be sent to the user? Or do we even care?
        return map(to_unicode, ifilter(bool, responses))


registry = Registry()


class Plugin(object):
    """
    The base class for helga plugins. There are three main methods of this base class that are
    important for creating class-based plugins.

    ``preprocess``

    Run by the plugin registry as a preprocessing mechanism. Allows plugins to modify
    the channel, nick, and/or message that other plugins will receive.

    ``process``

    Run by the plugin registry to allow a plugin to process a chat message. This is
    the primary entry point for plugins according to the plugin manager, so it should either return
    a response or not.

    ``run``

    Run internally by the plugin, generally from within the ``process`` method. This should
    do the actual work to generate a response. In other words, ``process`` should handle
    checking if the plugin should handle a message and then return whatever ``run`` returns.
    """
    #: The registered priority of the plugin
    priority = PRIORITY_NORMAL

    def __init__(self, priority=PRIORITY_NORMAL):
        self.priority = priority

    def run(self, client, channel, nick, message, *args, **kwargs):
        """
        Executes this plugin with a given message to generate a response. This should run without
        regard to whether it should or should not for a given message. Note, that this is where the
        actual work for the plugin should occur. Subclasses should implement this method.

        A return value of None, an empty string, or empty list implies that no response should be
        sent via chat. A non-empty string, list of strings, or raised :exc:`~helga.plugins.ResponseNotReady`
        implies a response to be sent.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: None if no response is to be sent back to the server, a non-empty string or list
                  of strings if a response is to be returned
        """
        return None  # pragma: no cover

    def preprocess(self, client, channel, nick, message):
        """
        A preprocessing filter for plugins. This allows a plugin to modify a received
        message prior to that message being handled by this plugin's or other plugin's
        ``process`` method.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: a three-tuple (channel, nick, message) containing any modifications
        """
        return channel, nick, message  # pragma: no cover

    def process(self, client, channel, nick, message):
        """
        This method of a plugin is called by helga's plugin registry to process an incoming
        chat message. This should determine whether or not the plugin ``run`` method should be
        called. If so, it should return whatever return value ``run`` generates. If not, ``None``
        should be returned.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: None if the plugin should not run, otherwise the return value of the ``run`` method
        """
        return self.run(client, channel, nick, message)

    def decorate(self, fn, preprocessor=False):
        """
        A helper for decorating a function to handle this plugin. This essentially just monkey
        patches the ``run`` or ``preprocess`` method whith the given function. Decorated functions
        should accept whatever arguments the subclass implementation sends to its ``run`` method.
        Also, instances/subclasses of :class:`Plugin` are kept in a list attribute of the decorated
        function. This allows chainable decorators that function as intended. Example usage::

            def my_plugin(*args, **kwargs):
                pass

            p = Plugin()
            p.decorate(my_plugin)
            assert p in my_plugin._plugins

        :param fn: function to decorate
        :param preprocessor: True if the function should be decorated as a preprocessor
        """
        if preprocessor:
            self.preprocess = fn
        else:
            self.run = fn

        try:
            fn._plugins.append(self)
        except AttributeError:
            fn._plugins = [self]

        return fn

    def __call__(self, client, channel, nick, message):
        """
        Proxy for ``process``
        """
        return self.process(client, channel, nick, message)


class Command(Plugin):
    """
    A subclass of :class:`Plugin` for command type plugins (see :ref:`plugins.types`). Command
    plugins have a default priority of :data:`~helga.plugins.PRIORITY_NORMAL`
    """

    #: The command string, i.e. 'search' for a command 'helga search foo'
    command = ''

    #: A list of command aliases. If a command 'search' has an alias list ['s'], then
    #: 'helga search foo' and 'helga s foo' will both run the command
    aliases = []

    #: An optional help string for the command. This is used by the builtin
    #: :ref:`builtin.plugins.help` plugin
    help = ''

    #: A boolean indicating whether or not to use shlex arg string parsing rather than naive
    #: whitespace splitting
    shlex = False

    def __init__(self, command='', aliases=None, help='', priority=PRIORITY_NORMAL, shlex=False):
        super(Command, self).__init__(priority)
        self.command = command or self.command
        self.aliases = aliases or self.aliases
        self.help = help or self.help
        self.shlex = shlex

    def parse(self, botnick, message):
        """
        Parse the incoming message using the current nick of the bot, the defined command string of
        this object, plus any aliases. Will return the actual command parsed (which could be an alias),
        plus either whitespaced delimited list of strings that follow the parsed command, or shlex
        argument list if ``shlex`` is True.

        Generally, this does not need to be implemented by subclasses

        :param botnick: the current bot nickname
        :param message: the incoming chat message
        :returns: two-tuple consisting of the string of parsed command, and an argument list of
                  strings either whitespace delimited or shlex split.
        """
        choices = [self.command] + list(self.aliases)

        # Sort choices from longest to shortest. This will ease a quirk where
        # short alias versions will trump the more verbose ones
        choices = sorted(choices, key=len, reverse=True)

        nick_prefix = ''

        # Handle multiple ways to parse this command
        prefix_botnick = getattr(settings, 'COMMAND_PREFIX_BOTNICK', None)
        if prefix_botnick is not None:
            fmt = '{0}\W*\s'
            if isinstance(prefix_botnick, basestring):
                nick_prefix = fmt.format(prefix_botnick)
            elif prefix_botnick:
                nick_prefix = fmt.format(botnick)

        prefixes = filter(bool, [nick_prefix, getattr(settings, 'COMMAND_PREFIX_CHAR', '!')])
        prefix = '({0})'.format('|'.join(prefixes))

        pat = ur'^{0}({1})($|\s(.*)$)'.format(prefix, '|'.join(choices))

        try:
            _, cmd, _, argstr = re.findall(pat, message, re.IGNORECASE)[0]
        except (IndexError, ValueError):
            # FIXME: Log here?
            return u'', []

        return cmd, filter(bool, self._parse_argstr(argstr))

    def _parse_argstr(self, argstr):
        """
        Parse an argument string for this command. If COMMAND_ARGS_SHLEX is set to False,
        then naive whitespace splitting is performed on the argument string. If not, a more robust
        ``shlex.split()`` is performed. For example, given the message::

            helga foo bar "baz qux"

        the former would produce arguments::

            ['bar', '"baz', 'qux"']

        while the latter would produce::

            ['bar', 'baz qux']

        """
        if self.shlex or settings.COMMAND_ARGS_SHLEX:
            argv = shlex.split(from_unicode(argstr.strip()))
        else:
            argv = argstr.strip().split(' ')

        return map(to_unicode, argv)

    def run(self, client, channel, nick, message, command, args):
        """
        Executes this plugin with a given message to generate a response. This should run without
        regard to whether it should or should not for a given message. Note, that this is where the
        actual work for the plugin should occur. Subclasses should implement this method.

        A return value of None, an empty string, or empty list implies that no response should be
        sent via chat. A non-empty string, list of strings, or raised :exc:`~helga.plugins.ResponseNotReady`
        implies a response to be sent.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :param cmd: The parsed command string which could be the registered command or one of the
                    command aliases
        :param args: The parsed command arguments as a list, i.e. any content following the command.
                     For example: ``helga foo bar baz`` would be ``['bar', 'baz']``
        :returns: String or list of strings to return via chat. None or empty string or list for no response
        """
        return None  # pragma: no cover

    def process(self, client, channel, nick, message):
        """
        Parses the incoming message and determins if this command should run (i.e. if the primary
        command or one of the aliases match).

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: None if the plugin should not run, otherwise the return value of the ``run`` method
        """
        command, args = self.parse(client.nickname, message)
        all_commands = [self.command] + list(self.aliases)

        if settings.COMMAND_IGNORECASE:
            command = command.lower()
            all_commands = map(methodcaller('lower'), all_commands)

        if command not in all_commands:
            return None

        return self.run(client, channel, nick, message, command, args)


class Match(Plugin):
    """
    A subclass of :class:`Plugin` for match type plugins (see :ref:`plugins.types`). Matches
    have a default priority of :data:`~helga.plugins.PRIORITY_LOW`
    """
    #: A regular expression string used to match against a chat message. Optionally, this attribute can
    #: be a callable that accepts a chat message string as its only argument and returns a value that
    #: can be evaluated for truthiness.
    pattern = ''

    def __init__(self, pattern='', priority=PRIORITY_LOW):
        super(Match, self).__init__(priority)
        self.pattern = pattern or self.pattern

    def run(self, client, channel, nick, message, matches):
        """
        Executes this plugin with a given message to generate a response. This should run without
        regard to whether it should or should not for a given message. Note, that this is where the
        actual work for the plugin should occur. Subclasses should implement this method.

        A return value of None, an empty string, or empty list implies that no response should be
        sent via chat. A non-empty string, list of strings, or raised :exc:`~helga.plugins.ResponseNotReady`
        implies a response to be sent.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :param matches: The result of ``re.findall`` if decorated with a regular expression, otherwise
                        the return value of the callable passed to :func:`helga.plugins.match`
        :returns: String or list of strings to return via chat. None or empty string or list for no response
        """
        return None  # pragma: no cover

    def match(self, message):
        """
        Matches a message against the pattern defined for this class. If the ``pattern`` attribute
        is a callable, it is called with the message as its only argument and that value is returned.
        Otherwise, the pattern attribute is used as a regular expression string argument to
        ``re.findall`` and that value is returned.

        :param message: the message received from the server
        :returns: the result of ``re.findall`` if pattern is a string, otherwise the return value of
                  calling the ``pattern`` attribute with the message as a parameter
        """
        if callable(self.pattern):
            fn = self.pattern
        else:
            fn = functools.partial(re.findall, self.pattern)

        try:
            return fn(message)
        except TypeError:
            return None

    def process(self, client, channel, nick, message):
        """
        Processes a message sent by a user on a given channel. This will return None if the message does
        not match the plugin's pattern, or the return value of ``run`` if it does match. For this plugin
        to match an incoming message, the return value of ``self.match()`` must return value that can
        be evaluated for truth. Generally, subclasses should not have to worry about this method, and
        instead, should focus on the implementation of ``run``.

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: None if the plugin should not run, otherwise the return value of the ``run`` method
        """
        matches = self.match(message)
        if not bool(matches):
            return None

        return self.run(client, channel, nick, message, matches)


def command(command, aliases=None, help='', priority=PRIORITY_NORMAL, shlex=False):
    """
    A decorator for creating command plugins

    :param command: The command string, i.e. 'search' for a command 'helga search foo'
    :param aliases: A list of command aliases. If a command 'search' has an alias list
                    ['s'], then 'helga search foo' and 'helga s foo' will both run the command.
    :param help: An optional help string for the command. This is used by the builtin help plugin.
    :param priority: The priority of the plugin. Default is :data:`~helga.plugins.PRIORITY_NORMAL`.
    :param shlex: A boolean indicating whether to use shlex arg string parsing rather than naive
                  whitespace splitting.

    Decorated functions should follow this pattern:

    .. function:: func(client, channel, nick, message, cmd, args)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :param cmd: The parsed command string which could be the registered command or one of the
                    command aliases
        :param args: The parsed command arguments as a list, i.e. any content following the command.
                     For example: ``helga foo bar baz`` would be ``['bar', 'baz']``
        :returns: String or list of strings to return via chat. None or empty string or list
                  for no response
    """
    return Command(command, aliases=aliases, help=help, priority=priority, shlex=shlex).decorate


def match(pattern, priority=PRIORITY_LOW):
    """
    A decorator for creating match plugins

    :param pattern: A regular expression string used to match against a chat message. Optionally,
                    this argument can be a callable that accepts a chat message string as its only
                    argument and returns a value that can be evaluated for truthiness.
    :param priority: The priority of the plugin. Default is :data:`~helga.plugins.PRIORITY_LOW`

    Decorated match functions should follow this pattern:

    .. function:: func(client, channel, nick, message, matches)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :param matches: The result of ``re.findall`` if decorated with a regular expression, otherwise
                        the return value of the callable passed
        :returns: String or list of strings to return via chat. None or empty string or list for no response
    """
    return Match(pattern, priority=priority).decorate


def preprocessor(priority=PRIORITY_NORMAL):
    """
    A decorator for creating preprocessor plugins

    :param priority: The priority of the plugin. Default is :data:`~helga.plugins.PRIORITY_NORMAL`

    Decorated preprocessor functions should follow this pattern:

    .. function:: func(client, channel, nick, message, matches)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param channel: The channel from which the message was received. This could be a public
                        channel like '#foo', or in the event of a private message, could be the
                        nick of the user sending the message
        :param nick: The nick of the user sending the message
        :param message: The full message string received from the server
        :returns: a three-tuple (channel, nick, message) containing any modifications
    """
    # This happens if not using a priority argument, but just decorating
    if callable(priority):
        return Plugin(priority=PRIORITY_NORMAL).decorate(priority, preprocessor=True)
    else:
        return functools.partial(Plugin(priority=priority).decorate, preprocessor=True)
