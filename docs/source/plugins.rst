.. _plugins:

Plugins
=======
One of the most prominent features of helga is its support for plugins and plugin architecture. At
their core, plugins are essentially standalone, installable python packages. There are few small
rules to follow, but creating custom plugins is an incredibly easy process.


.. _plugins.types:

Plugin Types
------------
Plugins have a notion of type. This essentially means that they have predefined expectations for
how they behave. At this time, there are three types of plugins:


Commands
^^^^^^^^
Plugins of this type require a user to specifically ask to perform some action. For example, a
command plugin behave like this::

    <sduncan> helga google something
    <helga> no results found for "something"

(see :ref:`plugins.creating.commands`)


Matches
^^^^^^^
Plugins of this type are intended to be a form of autoresponder that aim to provide some extra meaning
or context to what a user has said in a chat. For example, a match plugin could provide extra details if
someone says 'foo'::

    <sduncan> I'm talking about foo in this message
    <helga> sduncan just said 'foo'

(see :ref:`plugins.creating.matches`)


Preprocessors
^^^^^^^^^^^^^
Plugins of this type generally don't respond. However, they can modify the original message
that will be received by command or match plugins.

(see :ref:`plugins.creating.preprocessors`)


.. _plugins.priorities:

Plugin Priorities
-----------------
Plugins also have a notion of priority that affect the order in which the plugin manager will process
them. Priorities can be any numerical value, but as a rule of thumb, the higher the number, the more
*important* a plugin will be. More important plugins will be processed first. Note, however, that
preprocessor type plugins will *always* run before command and match plugins. Therefore, preprocessors
will only be weighted against other preprocessors. Commands and matches are weighted against other
commands and matches.

The :mod:`helga.plugins` module has three values that may be useful for indicating the priority
of a plugin:

* :const:`~helga.plugins.PRIORITY_LOW`
* :const:`~helga.plugins.PRIORITY_NORMAL`
* :const:`~helga.plugins.PRIORITY_HIGH`

The actual values of these priorities can be fine tuned via custom settings (see :ref:`config`).
Unless specifically indicated, each plugin type assumes a default priority:

* Preprocessors have a default priority of :const:`~helga.plugins.PRIORITY_NORMAL`
* Commands have a default priority of :const:`~helga.plugins.PRIORITY_NORMAL`
* Matches have a default priority of :const:`~helga.plugins.PRIORITY_LOW`


.. _plugins.creating:

Creating Plugins with Decorators
--------------------------------
Helga comes with an easy-to-use decorator API for writing simple plugins. For the most part, this
is the preferred way of creating custom plugins. In a nutshell, there are decorators in
:mod:`helga.plugins` that correspond to each plugin type:

* :func:`@command <helga.plugins.command>`
* :func:`@match <helga.plugins.match>`
* :func:`@preprocessor <helga.plugins.preprocessor>`


.. _plugins.creating.commands:

Command Plugins
^^^^^^^^^^^^^^^
Command plugins are those which require you to ask in order to perform some action. For these types
of plugins, you will use the :func:`@command <helga.plugins.command>` decorator:

.. autofunction:: helga.plugins.command
    :noindex:

For example::

    from helga.plugins import command

    @command('foo', aliases=['f'], help='The foo command')
    def foo(client, channel, nick, message, cmd, args):
        return u'You said "helga foo"'

For argument parsing, there are currently two supported behaviors. The default is to perform
whitespace splitting on the argument string. For example, given a command::

    helga foo bar "baz qux"

the resulting args list to the command function would be::

    ['bar', '"baz', 'qux"']

For some plugins, this may be less than ideal. Therefore, you can optionally pass ``shlex=True``
to the :func:`@command <helga.plugins.command>` decorator. This changes the behavior in such a way
that in the previous example, the resulting args list would be::

    ['bar', 'baz qux']

This behavior can also be configured globally by configuring ``COMMAND_ARGS_SHLEX = True``
in your settings file (see :ref:`config.default.plugins`)

.. important::

    Shlex argument parsing will become the default behavior in a future version of helga.


.. _plugins.creating.matches:

Match Plugins
^^^^^^^^^^^^^
Match plugins are those that are intended to be a form of autoresponder. They are meant to provide
some extra meaning or context to what a user has said in chat. For these types of plugins, you will
use the :func:`@match <helga.plugins.match>` decorator:

.. autofunction:: helga.plugins.match
    :noindex:

For example::

    from helga.plugins import match

    @match(r'foo')
    def foo(client, channel, nick, message, matches):
        return u'{0} said foo'.format(nick)

In most cases, this decorator will have a single regular expression as its argument. However, it
can also accept a callable. This callable should accept a single argument: the message contents
received from the chat server. There is no explicit return value type, but the return value should
be able to be evaluated for truthiness. When that return value has truth, then the decorated function
will be called. For example::

    import time
    from helga.plugins import match

    def match_even(message):
        if int(time.time()) % 2 == 0:
            return 'Even Time!'

    @match(match_even)
    def even(client, channel, nick, message, matches):
        # Will send 'Match: Even Time!' to the server
        return u'Match: {0}'.format(matches)


.. _plugins.creating.preprocessors:

Preprocessor Plugins
^^^^^^^^^^^^^^^^^^^^
Preprocessor plugins generally don't respond. Instead, they are intended to potentially
modify the original chat message that will be received by command or match plugins. For these
types of plugins, you will use the :func:`@preprocessor <helga.plugins.preprocessor>` decorator:

.. autofunction:: helga.plugins.preprocessor
    :noindex:

For example::

    from helga.plugins import preprocessor

    @preprocessor
    def foo(client, channel, nick, message):
        # Other plugins will think the message argument is what is returned
        return channel, nick, 'NOT THE ORIGINAL MESSAGE'


.. _plugins.creating.chaining:

Decorator Chaining
^^^^^^^^^^^^^^^^^^
The decorators for commands, matches, and preprocessors can be chained for more complex behavior.
For example, should you wish to have a command that could add or remove patterns for a match, you
could chain both :func:`@command <helga.plugins.command>` and :func:`@match <helga.plugins.match>`.
Note, however, that each plugin type decorator expects that decorated functions accept a specific
number of arguments. For this reason, it is best to use ``*args`` and argument length checking
(this may change in the future). For example, let's say we want a plugin that will match a dynamic
set of patterns, but also gives the ability to add or remove patterns and modifies the incoming
message by prepending text to indicate that it has been processed::

    import re
    from helga.plugins import command, match, preprocessor

    PATTERNS = set()

    def check(message):
        global PATTERNS
        return re.findall('({0})'.format('|'.join(PATTERNS)))

    @preprocessor
    @match(check)
    @command('matcher', help='Usage: helga (add|remove) <pattern>')
    def matcher(client, channel, nick, message, *args):
        global PATTERNS

        if len(args) == 0:
            # Preprocessor
            return channel, nick, u'[matcher] {0}'.format(message)
        elif len(args) == 1:
            # Match - args[0] is return value of check(), re.findall
            found_list = args[0]
            return u'What you said matched: {0}'.format(found_list)
        elif len(args) == 2:
            # Command: args[1] is the parsed argument string
            command, pattern = args[1][:2]
            if command == 'add':
                PATTERNS.add(pattern)
                return u'Added {0}'.format(pattern)
            else:
                PATERNS.discard(pattern)
                return u'Removed {0}'.format(pattern)

Note, decorator chaining is only one way to create complex behavior for plugins. There is
also a class-based plugin API (see :ref:`plugins.advanced`)


.. _plugins.unicode:

Handling Unicode
----------------
Plugins should try to deal exclusively with unicode as much as possible. This is important to keep
in mind since all plugins that accept string arguments will receive unicode strings specifically
and not byte strings. For the most part, helga's client connection assumes a UTF-8 encoding for all
incoming messages. Note, though, that plugins that don't explicitly return unicode responses will not fail;
the internal plugin manager will implicitly handle convertng all responses to the correct format
(unicode or byte strings) needed by the chat server. There are also useful utilities for dealing with
unicode support in plugins found in :mod:`helga.util.encodings`:

* :func:`from_unicode <helga.util.encodings.from_unicode>`
* :func:`from_unicode_args <helga.util.encodings.from_unicode_args>`
* :func:`to_unicode <helga.util.encodings.to_unicode>`
* :func:`to_unicode_args <helga.util.encodings.to_unicode_args>`


.. _plugins.database:

Accessing The Database
----------------------
As mentioned in :ref:`getting_started.requirements`, MongoDB is highly recommended, but not
required dependency. Having a MongoDB server that helga can use means that plugins can store
data for use across restarts. This may be incredibly useful depending on the needs of your
plugin. If your MongoDB connection is configured properly according to :ref:`helga.settings.core`,
two `pymongo`_ objects in :mod:`helga.db` will be available for use:

* :obj:`helga.db.client`: A pymongo `MongoClient`_ object, the connection client to MongoDB
* :obj:`helga.db.db`: A pymongo `Database`_ object, the default MongoDB database to use

Using this database connection in a plugin is very simple::

    from helga.db import db

    db.my_collection.insert({'foo': 'bar'})
    db.my_collection.find()

For more information on using this, see the `pymongo`_ API documentation.

.. note::

  Should helga not be configured properly for MongoDB, or should a connection to MongoDB fail,
  the database object :obj:`helga.db.db` will explicitly be ``None``. Therefore, it may be important
  for plugins that depend on MongoDB to check for this condition.


.. _plugins.settings:

Requiring Settings
------------------
In many instances, plugins may require some configurable setting in a custom helga settings
file (see :ref:`config.custom`). As a general rule of thumb, configurable settings should
be documented by a plugin but in no way should expect that they be present in ``helga.settings``.
Plugins should use ``getattr`` for retrieving custom settings and assume some default value::

    from helga import settings

    my_setting = getattr(settings, 'MY_SETTING_VALUE', 42)

Also, although not explicitly required, settings names should be prefixed with the name of the
plugin. This should help in organizing custom settings. For example, if a plugin ``foo`` uses
a custom setting ``SOME_VALUE``, then try to expect a setting ``FOO_SOME_VALUE``.


.. _plugins.async:

Communicating Asynchronously
----------------------------
In some cases, plugins may need to perform some blocking action such as communicating with an
external API. If a plugin were to perform this action and directly return a string response,
this may block other plugins from processing. To get around this concern, plugins can, instead
of returning a response, raise :exc:`~helga.plugins.ResponseNotReady`.
This will indicate to helga's plugin manager that a response may be sent at some point in the
future. In this instance, helga will continue to process other plugins, unless configured to only
return first response, in which case no other plugins will be processed (see :ref:`config.default.plugins`).
For example::

    from helga.plugins import command, ResponseNotReady

    @command('foo')
    def foo(client, channel, nick, message, cmd, args):
        # Run some async action
        raise ResonseNotReady

In order to actually invoke some asynchronous action, most plugins can and should utilize the
fact that helga is built using `Twisted`_ by calling ``twisted.internet.reactor.callLater``.
For example::

    from twisted.internet import reactor

    def do_something(arg, kwarg=None):
        print arg or kwarg

    # Have the event loop run `do_something` in 30 seconds
    reactor.callLater(30, do_something, None, kwarg='foo')

For more details on this see the `Twisted Documentation`_. To revisit the previous plugin example::

    from twisted.internet import reactor
    from helga.plugins import command, ResponseNotReady

    def foo_async(client, channel, args):
        client.msg(channel, 'someone ran the foo command with args: {0}'.format(args))

    @command('foo')
    def foo(client, channel, nick, message, cmd, args):
        reactor.callLater(5, foo_async, client, channel, args)
        raise ResonseNotReady

Notice above that the callback function ``foo_async`` takes the client connection as an argument.
Should a plugin need to respond asynchronously to the server, it is generally a good idea for deferred
callbacks to accept at a minimum the client and the channel of the message. In addition, there
are several useful methods of both :class:`helga.comm.irc.Client` and :class:`helga.comm.xmpp.Client`
that can be used for asynchronous communication:

* :meth:`helga.comm.irc.Client.msg`
* :meth:`helga.comm.irc.Client.me`
* :meth:`helga.comm.xmpp.Client.msg`
* :meth:`helga.comm.xmpp.Client.me`


.. _plugins.signals:

Signals/Notifications of Helga Events
-------------------------------------
Helga makes heavy use of signals for events provided by `smokesignal`_. In this way, plugins
can receive notifications when some event occurs and perform some action such as loading data
from the database or setting some preferred state. At this time, there are several included
signals that fire on given events and provide callbacks with certain arguments:

``started``
    Fired when the helga process starts. Callbacks should accept no arguments.

``signon``
    Fired when helga successfully connects to the chat server. Callbacks should follow:

    .. function:: func(client)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
                       depending on the server type

``join``
    Fired when helga joins a channel. Callbacks should follow:

    .. function:: func(client, channel)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
                       depending on the server type
        :param channel: the name of the channel

``left``
    Fired when helga leaves a channel. Callbacks should follow:

    .. function:: func(client, channel)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
                       depending on the server type
        :param channel: the name of the channel

``user_joined``
    Fired when a user joins a channel helga is in. Callbacks should follow:

    .. function:: func(client, nick, channel)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
                       depending on the server type
        :param nick: the nick of the user that joined
        :param channel: the name of the channel

``user_left``
    Fired when a user leaves a channel helga is in. Callbacks should follow:

    .. function:: func(client, nick, channel)
        :noindex:

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
                       depending on the server type
        :param nick: the nick of the user that left
        :param channel: the name of the channel



.. _plugins.packaging:

Packaging and Distribution
--------------------------
If you have created a simple helga plugin, you may be asking "What now?". Helga, rather than using
plugin directories containing lots of one-off scripts, makes use of proper python packaging to manage
plugin installation. This may be a bit of an advanced topic if you are new to python packaging,
but for the most part, you can follow a small number of repeatable steps for simple plugins.


.. _plugins.packaging.structure:

Basic Project Structure
^^^^^^^^^^^^^^^^^^^^^^^
For the most part, simple plugins will follow the same basic project structure::

    helga_my_plugin
    ├── helga_my_plugin.py
    ├── LICENSE
    ├── MANIFEST.in
    ├── README.rst
    ├── setup.py
    ├── tests.py
    └── tox.ini

``helga_my_plugin.py``
    This is the actual plugin script. This can be named whatever you feel like naming it,
    but it is good practice to name this something like ``helga_<name of plugin>.py``.

``LICENSE``
    Since helga is dual-licensed MIT and GPL, this can be either MIT or GPL

``MANIFEST.in``
    If you wish to include any non-python files with your plugin, you should include this
    file. For example, if you wish to include the README and LICENSE, the contents of this file
    would be::

        LICENSE
        README.rst

``README.rst``
    Not required to be a reStructuredText document, but it is good practice to describe
    what the plugin does, how to use it, and if there are any custom settings that should be set.

``setup.py``
    setuptools setup script (see :ref:`plugins.packaging.setuptools`)

``tests.py``
    If you write any unit tests for your plugin

``tox.ini``
    If you write any unit tests for your plugin and use `tox`_ to run them. It is generally a good
    idea to use tox to run tests against python 2.6 and 2.7 since helga supports both of those versions.


.. _plugins.packaging.setuptools:

``setuptools`` and ``entry_points``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Not only does a plugin's setup.py file declare project information and allow it to be installed with
pip, it is also how helga loads plugins at runtime. To do this, helga uses a setuptools feature known as
`entry_points`_. To understand how to use this, take the above project structure as an example. Let's
say that the contents of ``helga_my_plugin.py`` looks like this::

    from helga.plugins import match

    @match(r'foo')
    def foo(client, channel, nick, message, matches):
        return u'{0} said foo'.format(nick)

A basic ``setup.py`` file for this project might look like:

.. code-block:: python

    from setuptools import setup, find_packages

    setup(
        name='helga_my_plugin',
        version='0.0.1',
        description='A foo plugin',
        author="Jane Smith"
        author_email="jane.smith@example.com",
        packages=find_packages(),
        py_modules=['helga_my_plugin'],
        include_package_data=True,
        zip_safe=True,
        entry_points=dict(
            helga_plugins=[
                'my_plugin = helga_my_plugin:foo',
            ],
        ),
    )

Before talking about ``entry_points``, take note of some other important lines.

``py_modules``
    If your plugin is a single python file, you will need include it without the '.py' extension
    in a string list.

``include_package_data``
    If you intend on including files specified in a ``MANIFEST.in`` file, you will need to set this
    to True.

Now, let's talk about the ``entry_points`` line. The helga plugin loader will look for any installed
python package that declares ``helga_plugins`` entry points. These should be list of strings of the
form::

    plugin_name = module.path:decorated_function

The 'plugin_name' portion should be a simple name for the plugin, such as 'my_plugin' in the
'helga_my_plugin' example above. The latter half must be colon delimited containing a module path
and the function decorated using :func:`@command <helga.plugins.command>`, :func:`@match <helga.plugins.match>`,
or :func:`@preprocessor <helga.plugins.preprocessor>`. So if a file ``helga_my_plugin.py`` contains::

    from helga.plugins import match

    @match(r'foo')
    def foo(*args):
        return 'foo'

the entry point would be ``helga_my_plugin:foo``. For more information and details on how entry
points work, see the `entry_points`_ documentation.


.. _plugins.packaging.distribution:

Distributing Plugins
^^^^^^^^^^^^^^^^^^^^
The preferred distribution channel for helga plugins is `PyPI`_ so that plugins can be installed
using pip. Once you have properly packaged your plugin, submit it to PyPI:

.. code-block:: bash

    $ python setup.py sdist register upload


.. _plugins.packaging.cookiecutter:

Using A Project Template
^^^^^^^^^^^^^^^^^^^^^^^^
If you use `cookiecutter`_ for managing project templates, there is a third-party helga plugin
cookiecutter template here: https://github.com/bigjust/cookiecutter-helga-plugin


.. _plugins.installing:

Installing Plugins
------------------
If plugins are properly packaged and distributed according to :ref:`plugins.packaging`, then
any new plugins for helga to use can be installed using pip. If helga has been installed into
a virtualenv as mentioned in :ref:`getting_started`, activate that virtualenv prior to installing
the new plugin:

.. code-block:: bash

    $ source bin/activate
    $ pip install helga-my-plugin

Note, however, that you will need to full restart any running helga process in order to use the
new plugins. This behavior may change in future versions of helga. If a plugin is not distributed
using PyPI, but is available via some source repository, you can still install it with a little more
work:

.. code-block:: bash

    $ source bin/activate
    $ git clone git@example.com:janedoe/helga-my-plugin.git src/helga-my-plugin
    $ cd src/helga-my-plugin
    $ python setup.py develop

Note, that installing a plugin will mean that it will be loaded when helga starts unless it is
not included in the plugins whitelist :data:`helga.settings.ENABLED_PLUGINS`
or it is listed in the plugins blacklist :data:`helga.settings.DISABLED_PLUGINS`
The default behavior is that all plugins installed on the system are loaded and made available
for use in IRC.

With this in mind, installed plugins are available for use, but they may not immediately be so.
Helga maintains a list of plugin names that indicate which plugins should be enabled by default
in a channel, which is configured via :data:`helga.settings.DEFAULT_CHANNEL_PLUGINS`.
If a plugin name does not appear in this list, a user in a channel will not be able to use it until
it is enabled with the :ref:`builtin.plugins.manager` plugin::

    <sduncan> !plugins enable my_plugin


.. _plugins.advanced:

Class-Based Plugins
-------------------
All of the above documentation for creating plugins makes use of helga's simple decorator API.
Generally speaking, the decorator API is the preferred way of authoring plugins. However, simple
decorated functions may not be robust enough for all plugins. For this reason, there is a class-based
API that can be used instead. In fact, this is what is used behind the scenes for the decorator API.


.. _plugins.advanced.base:

Base Plugin Class
^^^^^^^^^^^^^^^^^
At a high level, plugin objects should be some form of a sublass of :class:`helga.plugins.Plugin`:

.. autoclass:: helga.plugins.Plugin
    :noindex:
    :members: preprocess, process, run

Plugin implementations can subclass this base class directly, but there are convenience subclasses
for each plugin type that already do a lot of the heavy lifting.


.. _plugins.advanced.command:

Command Subclasses
^^^^^^^^^^^^^^^^^^
To create a class-based command plugin, subclass :class:`helga.plugins.Command`. For example::

    from helga.plugins import Command

    class FooCommand(Command):
        command = 'foo'
        aliases = ['f']
        help = 'Return the foo count. Usage: helga (foo|f)'

        def __init__(self, *args, **kwargs):
            super(FooCommand, self).__init__(*args, **kwargs)
            self.foo_count = 0

        def run(self, client, channel, nick, message, cmd, args):
            self.foo_count += 1
            return u'Foo count is {0}'.format(self.foo_count)


.. _plugins.advanced.match:

Match Subclasses
^^^^^^^^^^^^^^^^
To create a class-based match plugin, subclass :class:`helga.plugins.Match`. For example::

    from helga.plugins import Match

    class FooMatch(Match):
        pattern = r'foo (\w+)'

        def run(self, client, channel, nick, message, matches):
            return u"{0} said 'foo' followed by '{1}'".format(nick, matches[0])

Or in the case of using a callable as a pattern::

    import time

    from helga.plugins import Match

    class FooMatch(Match):

        def __init__(self, *args, **kwargs):
            super(FooMatch, self).__init__(*args, **kwargs)
            self.pattern = self.match_foo

        def match_foo(self, message):
            if 'foo' in message:
                return time.time()

        def run(self, client, channel, nick, message, matches):
            return u"{0} said 'foo' at {0}".format(nick, matches)


.. _plugins.advanced.preprocessor:

Preprocessor Subclasses
^^^^^^^^^^^^^^^^^^^^^^^
There is no direct :class:`Plugin <helga.plugins.Plugin>` subclass for preprocessor plugins.
Preprocessors using the decorator API are merely instances of the base :class:`Plugin <helga.plugins.Plugin>`
class (see :ref:`plugins.advanced.base`). However, to create a preprocessor plugin using a
class-based approach::

    from helga.plugins import Plugin

    def FooPreprocessor(Plugin):

        def preprocess(self, client, channel, nick, message):
            # Ignore anything from nicks that start with a vowel
            if nick[0] in 'aeiou':
                return channel, nick, u''
            return channel, nick, message


.. _plugins.advanced.packaging:

Packaging Class-Based Plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Class-based plugins are packaged in exactly the same manner as those using the decorator API (see
:ref:`plugins.packaging`). The only difference is with respect to entry points. Whereas with decorator
plugins, the entry point follows a 'module:function' pattern, class-based plugins follow a
'module:class' pattern. For example, given this plugin in a file ``helga_foo.py``::

    from helga.plugins import Command

    class FooCommand(Command):
        pass

The respective entry point string might look something like this::

    foo = helga_foo:FooCommand



.. _plugins.xmpp:

Supporting XMPP
---------------
You shouldn't need to make any special changes to plugins if you follow the documenation above. However,
remember that helga was started as an IRC bot, so things work a bit more to that favor. Plugins will
still receive ``client``, ``channel``, ``nick``, and ``message`` arguments.

Note, though, that values for ``channel`` will **never** be the full JID of a chat room. Instead, they
will be the ``user`` portion of the room JID, prepended with a '#'. For example::

    bots@conf.example.com

would become a channel named ``#bots`` and private messages from::

    user@host.com

would become a channel named ``user``.

Nick values operate in a similar manner, only using the ``resource`` portion of the JID for group chat.
For example::

    bots@conf.example.com/foo

would become a nick named::

    foo

and a private message from::

    foo@host.com

would become a nick named::

    foo

For more information about how this works see :meth:`helga.comm.xmpp.Client.parse_channel` and
:meth:`helga.comm.xmpp.Client.parse_nick`.



.. _`pymongo`: http://api.mongodb.org/python/current/
.. _`MongoClient`: http://api.mongodb.org/python/current/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
.. _`Database`: http://api.mongodb.org/python/current/api/pymongo/database.html#pymongo.database.Database
.. _`tox`: https://tox.readthedocs.org/en/latest/
.. _`entry_points`: https://pythonhosted.org/setuptools/setuptools.html#dynamic-discovery-of-services-and-plugins
.. _`cookiecutter`: http://cookiecutter.readthedocs.org/en/latest/
.. _`PyPI`: https://pypi.python.org/pypi
.. _`Twisted`: https://twistedmatrix.com/trac/
.. _`Twisted Documentation`: https://twistedmatrix.com/trac/wiki/Documentation
.. _`smokesignal`: https://github.com/shaunduncan/smokesignal
