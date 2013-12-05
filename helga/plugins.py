import functools
import logging
import pkg_resources
import re

from collections import defaultdict


logger = logging.getLogger(__name__)


class Registry(object):
    """
    Simple plugin registry that handles dispatching messages to registered plugins.
    Plugins can be disabled per channel. By default, plugins are loaded, but not
    enabled unless ENABLED_PLUGINS is set in helga settings. This is done so that
    potentially annoying plugins can be enabled on-demand
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Only here so we only maintain one registry for the life of the application. There
        is some state-specific things that shouldn't be lost in the event the IRC client
        loses the connection to the server
        """
        if cls.__instance is None:
            cls.__instance = super(Registry, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        if not hasattr(self, 'plugins'):
            self.plugins = {}

        if not hasattr(self, 'enabled_plugins'):
            self.enabled_plugins = defaultdict(set)

    def register(self, name, fn_or_cls):
        # Make sure we're working with an instance
        try:
            if issubclass(fn_or_cls, Plugin):
                fn_or_cls = fn_or_cls()
        except TypeError:
            pass

        if not isinstance(fn_or_cls, Plugin) and not hasattr(fn_or_cls, 'process'):
            raise TypeError("Plugin %s must be a subclass of Plugin, or a decorated function" % name)

        self.plugins[name] = fn_or_cls

    def disable(self, channel, *plugins):
        self.enabled_plugins[channel] = self.enabled_plugins[channel].difference(plugins)

    def enable(self, channel, *plugins):
        self.enabled_plugins[channel].union(plugins)

    def load(self):
        """
        Locate all setuptools entry points by the name 'helga_plugins'
        and initialize them. Any third-party library may register a plugin by
        addint the following to their setup.py::

            entry_points = {
                'helga_plugins': [
                    'plugin_name = mylib.mymodule:MyPluginClass',
                ],
            },

        """
        for entry_point in pkg_resources.iter_entry_points(group='helga_plugins'):
            try:
                logger.debug('loading entry_point %s' % entry_point.name)
                self.register(entry_point.name, entry_point.load())
            except Exception:
                logger.exception("Error initializing plugin %s" % entry_point)

    def process(self, client, channel, nick, message):
        responses = []

        for name in self.enabled_plugins[channel]:
            if name not in self.plugins:
                logger.debug('Plugin %s is enabled on %s, but not loaded' % (name, channel))
                continue

            try:
                resp = self.plugins[name].process(client, channel, nick, message)
            except:
                logger.exception("Calling process on plugin %s failed" % name)
                resp = None

            if resp is not None:
                responses.append(resp.strip())

        return filter(bool, responses)


class Plugin(object):
    """
    Base class for creating helga plugins. Plugins have a minimal API, and there
    are essentially two methods that require some implementation, ``__call__`` and
    ``run``. Although these methods may seem to have a similar meaning, they both
    have different purposes. An implementation for ``__call__`` is required by helga's
    plugin registry, since it expects plugins to be callable. The call arguments are
    expected to be consistent for all plugin implementations. On the other hand, the
    ``run`` method is used to do the actual legwork for a plugin. At a minimum, this
    should accept the same arguments as ``__call__`` but subclasses my define any additional
    arguments if necessary.

    In other words, ``__call__`` should decide if a message is worthy of a response, and
    ``run`` should provide the response. As a simple example::

        import time

        class MyPlugin(Plugin):
            def run(self, channel, nick, message):
                return 'Current timestamp: %d' % time.time()

            def __call__(self, channel, nick, message):
                if message.startswith('!time'):
                    return self.run(channel, nick, message)
    """
    def run(self, client, channel, nick, message, *args, **kwargs):
        """
        Runs the plugin to generate a response. At a minimum this should accept
        three arguments. It should also either return None, if no response is to be
        sent back over IRC, or a non-empty string.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        """
        return None

    def process(self, client, channel, nick, message):
        """
        This is the global entry point for plugins according to helga's plugin registry.
        Each plugin will be called when a message is received over IRC with the channel
        in which the message was received, the nick of the user that sent the message, and
        the message itself. Much like ``run``, this should either return None, if no
        response is to be sent back over IRC, or a non-empty string. In most cases, this
        should just return whatever the return value of calling ``self.run`` is.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        """
        return self.run(client, channel, nick, message)

    def decorate(self, fn):
        """
        A helper used for establishing decorators for plugin classes. This does nothing
        more than monkey patch the ``run`` method of the instance with whatever function
        is being decorated. Note that the decorated function should accept whatever arguments
        the subclass implementation sends to its ``run`` method.
        """
        self.run = fn
        fn.process = self
        return fn

    def __call__(self, client, channel, nick, message):
        """
        Proxy for ``process``
        """
        return self.process(client, channel, nick, message)


class Command(Plugin):
    """
    A command is a type of plugin which requries a user to specifically ask
    for some action. This can be something simple like "helga haiku" or
    "helga google airspeed velocity of an unladen swallow".

    Command subclasses must provide three class-level attributes to function
    properly:

    - **command**: The command string that invokes this action
    - **aliases**: An optional list of string aliases that can also invoke this command
    - **help**: Useful help string on how to use this command

    In addition to these attributes, subclasses must also implement a ``run`` method
    that accepts six arguments:

    - **client**: an instance of :class:`helga.comm.Client`
    - **channel**: the channel on which the message was received
    - **nick**: the current nick of the message sender
    - **message**: the message string itself
    - **command**: the parsed command, which is either the preferred command or a command alias
    - **args**: a list of strings, space delimited, that follow the command

    The following is a simple example::

        class Haiku(Command):
            command = 'foo'
            aliases = ('bar',)
            help = 'Responds to `helga foo` with the string bar'

            def run(self, channel, nick, message, command, args):
                return 'bar'

    Using the above example may produce the following results in IRC::

        <sduncan> helga foo
        <helga> sduncan said foo
        <sduncan> helga bar
        <helga> sduncan said bar
    """

    command = ''
    aliases = []
    help = ''

    def __init__(self, command='', aliases=None, help=''):
        self.command = command or self.command
        self.aliases = aliases or self.aliases
        self.help = help or self.help

    def parse(self, botnick, message):
        """
        Parse the incoming message using the current nick of the bot, the defined
        command string of this object, plus any aliases. Will return the actual
        command parsed (which could be an alias), plus whitespaced delimited list
        of strings that follow the parsed command.

        :param botnick: helga's current nickname
        :param message: the incoming IRC message
        :returns: string of parsed command, whitespaced delimited string list of args
        """
        choices = [self.command] + list(self.aliases)
        pat = r'%s\W*\s(%s)\s?(.*)$' % (botnick, '|'.join(choices))
        try:
            cmd, argstr = re.findall(pat, message)[0]
        except (IndexError, ValueError):
            # FIXME: Log here?
            return u'', []

        return cmd, argstr.strip().split(' ')

    def run(self, client, channel, nick, message, command, args):
        """
        This is where any actual work should be done for a command. Generally, this
        is only used for subclasses of the base Command class. The @command decorator
        will monkey patch this method with whatever the decorated function is.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        :param command: the parsed command, which is either the preferred command or a command alias
        :param args: a list of strings, space delimited, that follow the command
        """
        return None

    def process(self, client, channel, nick, message):
        """
        Processes a message sent by a user on a given channel. This will return
        None if this command should respond to the incoming message, or if there
        is an exception raised from calling the ``run`` method or attribute of the
        instance.

        Generally, subclasses should not have to worry about this method, and
        instead, should focus on the implementation of ``run``, which is called should
        this command be invoked.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        """
        command, args = self.parse(client.nickname, message)
        if command != self.command and command not in self.aliases:
            return None

        try:
            return self.run(client, channel, nick, message, command, args)
        except (NotImplementedError, TypeError):
            # FIXME: Log warning here
            return None


class Match(Plugin):
    """
    A match is a type of plugin that will make helga respond if the contents
    of a user's message match a pattern. For example, if a match plugin looks
    for the string "foo", helga will respond with "bar" without being asked
    to do so. Subclasses must provide one class-level attribute:

    - **pattern**: either a valid regex pattern string, or a callable

    If the match pattern is a callable, it must accept a single string argument,
    which will be the IRC message to check, and it must return a value that can be
    evaluated as either True or False via bool(). Good practice here is to
    return the list of strings that were matched or found, but this is not
    required.

    In addition to this class attribute, subclasses must also implement a ``run``
    method that accepts five arguments:

    - **client**: an instance of :class:`helga.comm.Client`
    - **channel**: the channel on which the message was received
    - **nick**: the current nick of the message sender
    - **message**: the message string itself
    - **matches**: if the ``pattern`` attribute is a callable, this will be its return value,
      otherwise it will be the return value of ``re.findall``.

    The following is a simple example::

        class FooMatch(Match):
            pattern = r'foo-(\d+)'

            def run(self, channel, nick, message, matches):
                return '%s is talking about foo thing %s' % (nick, matches[0])

    Using the above example may produce the following results in IRC::

        <sduncan> this is about foo-123
        <helga> sduncan is talking about foo thing 123
    """
    pattern = ''

    def __init__(self, pattern=''):
        self.pattern = pattern or self.pattern

    def run(self, client, channel, nick, message, matches):
        """
        This is where any actual work should be done for a command. Generally, this
        is only used for subclasses of the base Command class. The @command decorator
        will monkey patch this method with whatever the decorated function is.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        :param matches: if the ``pattern`` attribute of this class is a callable, this will be its
                        return value, otherwise it will be the return value of ``re.findall``
        """
        return None

    def match(self, message):
        """
        Matches a message against the pattern defined for this class. If the pattern attribute
        is a callable, it is called with the message as its only argument and that value is returned.
        Otherwise, the pattern attribute is used as a regular expression string argument to
        ``re.findall`` and that value is returned.

        :param message: the message received over IRC
        """
        if callable(self.pattern):
            fn = self.pattern
        else:
            fn = functools.partial(re.findall, self.pattern)

        try:
            return fn(message)
        except TypeError:
            # FIXME: Log warning here
            pass

        return None

    def process(self, client, channel, nick, message):
        """
        Processes a message sent by a user on a given channel. This will return
        None if the message does not match the plugin's pattern, or a non-empty string
        (the return value of ``run``) if it does match.

        Generally, subclasses should not have to worry about this method, and
        instead, should focus on the implementation of ``run``, which is called should
        the incoming message be matched against the plugin's pattern.

        :param client: an instance of :class:`helga.comm.Client`
        :param channel: the channel on which the message was received
        :param nick: the current nick of the message sender
        :param message: the message string itself
        """
        matches = self.match(message)
        if not bool(matches):
            return None

        try:
            return self.run(channel, nick, message, matches)
        except TypeError:
            # FIXME: Log warning here
            return None


def command(command, aliases=None, help=''):
    """
    A decorator for creating simple commands where subclassing the ``Command``
    plugin type may be overkill. This is generally the easiest way to create helga
    commands. However, decorated functions must adhere to accepting six arguments:

    - **client**: an instance of :class:`helga.comm.Client`
    - **channel**: the channel on which the message was received
    - **nick**: the current nick of the message sender
    - **message**: the message string itself
    - **command**: the parsed command, which is either the preferred command or a command alias
    - **args**: a list of strings, space delimited, that follow the command

    The decorated function must return a string or None. If the return value is an empty string or
    None, then no response will be sent over IRC. A simple command example::

        @command('foo', aliases=('bar', 'baz'))
        def foo(client, channel, nick, message, command, args):
            return '%s said %s' % (nick, command)

    Using the above example may produce the following results in IRC::

        <sduncan> helga foo
        <helga> sduncan said foo
        <sduncan> helga bar
        <helga> sduncan said bar
    """
    return Command(command, aliases=aliases, help=help).decorate


def match(pattern=''):
    """
    A decorator for creating simple regex matches where subclassing the ``Match``
    plugin type may be overkill. This is generally the easiest way to create helga
    match plugins. However, decorated functions must adhere to accepting five arguments:

    - **client**: an instance of :class:`helga.comm.Client`
    - **channel**: the channel on which the message was received
    - **nick**: the current nick of the message sender
    - **message**: the message string itself
    - **matches**: if the ``pattern`` attribute is a callable, this will be its return value,
      otherwise it will be the return value of ``re.findall``.

    The decorated function must return a string or None. If the return value is an empty string or
    None, then no response will be sent over IRC. A simple command example::

        @match('foo')
        def foo(client, channel, nick, message, matches):
            return '%s said foo' % nick

    Using the above example may produce the following results in IRC::

        <sduncan> i am talking about foo here
        <helga> sduncan said foo
    """
    return Match(pattern).decorate
