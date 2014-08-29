helga
=====

.. image:: https://travis-ci.org/shaunduncan/helga.png
    :target: https://travis-ci.org/shaunduncan/helga

.. image:: https://coveralls.io/repos/shaunduncan/helga/badge.png?branch=master
    :target: https://coveralls.io/r/shaunduncan/helga?branch=master

.. image:: https://badge.fury.io/py/helga.png
    :target: http://badge.fury.io/py/helga

.. image:: https://pypip.in/d/helga/badge.png
    :target: https://pypi.python.org/pypi/helga


About
-----

A python-based IRC bot using Twisted. Original inspiration came
from `olga`_. Why re-implement another bot? Because olga is written
in perl, and I wanted something a bit more sane to look at.

.. _`olga`: https://github.com/thepeopleseason/olga


Requirements
------------

All requirements for helga are listed in ``requirements.txt``.
However, there is a single external requirement, and that is MongoDB.
You don't need it, per se, but many of the included plugins use MongoDB
for storing consistent state between restarts.


Getting Started
---------------

Start by creating a virtualenv where helga will reside:

.. code-block:: bash

    $ virtualenv helga
    $ cd helga
    $ source bin/activate

Then grab the latest copy and install requirements:

.. code-block:: bash

    $ git clone https://github.com/shaunduncan/helga src/helga
    $ cd src/helga
    $ python setup.py develop
    $ pip install -r requirements.txt

Once you have performed the above steps, there will be a ``helga`` executable
placed in the ``bin`` dir of your virtualenv. Run helga by calling this:

.. code-block:: bash

    $ /path/to/venv/bin/helga

Note that this uses the default settings file, ``helga.settings`` to start.
You can, and should, use your own custom setttings. This file must a be an
importable python file on $PYTHONPATH. To run helga with your custom settings
file, set an environment variable ``HELGA_SETTINGS`` to be a python import path:

.. code-block:: bash

    $ export HELGA_SETTINGS=path.to.mysettings

This will preserve any defaults in ``helga.settings``, but you can override at will.

Local Development
+++++++++++++++++

The included Vagrantfile will let you spin up a VM to run both MongoDB and an IRC server
for local development. Once you've followed the previous instructions for installing helga,
simply ``vagrant up``. This will forward host ports 6667 (irc) and 27017 (mongo) to the guest.
At this point, simply runing ``helga`` from the command line will connect to this VM.


Plugins
-------

Overview
++++++++

Helga supports plugins outside of the core source code. Plugins have a minimal API, but there
are some basic rules that should be followed. All core plugin implementations can be found
in ``helga.plugins.core``. The basic requirement for plugins is that they have a ``process``
attribute that is a callable and determines if the plugin should handle a message, and
a ``run`` method that actually performs the legwork of what the plugin should do. By convention,
the ``process`` method should accept four arguments:

- **client**: an instance of ``helga.comm.Client``
- **channel**: the channel on which the message was received
- **nick**: the current nick of the message sender
- **message**: the message string itself

The ``run`` is a bit different as it is up to the plugin implementation itself to decide what
arguments are necessary to generate a response. This method should be called by ``process`` and
should return one of:

- None or empty string, if no response is to be sent over IRC
- Non-empty string for a single line response
- List of strings for multiline responses

Really, as long as you follow the above conventions, you can write plugins however you wish.
However, you should try to keep plugins simple and use the included decorators ``command``,
``match``, and ``preprocessor`` (explained later). However, if you prefer writing a plugin
as a class, you can subclass the included ``Plugin`` base class, provided you have followed
the above rules. Here is a simple example:

.. code-block:: python

    import time
    from helga.plugins.core import Plugin

    class MyPlugin(Plugin):
        def run(self, channel, nick, message):
            return u'Current timestamp: {0}'.format(time.time())

        def process(self, channel, nick, message):
            if message.startswith('!time'):
                return self.run(channel, nick, message)

**NOTE** the previous example is not the preferred way. You should use the included
decorators instead (shown below).

A Tale of Unicode
~~~~~~~~~~~~~~~~~

Plugins should try to deal with unicode as much as possible. This is important as all arguments
a plugin receives will be unicode strings and not byte strings. This process happens automatically
as all strings received over IRC are decoded as UTF-8 an converted to unicode. If a plugin returns
a string response that is unicode, it will be encoded as UTF-8 prior to being sent over IRC. To
help deal with this, there are two helpful methods in ``helga.util.encodings`` to convert to/from
unicode: ``to_unicode`` and ``from_unicode``.

Plugin Types
++++++++++++

For the most part, there are two main types of plugins: commands and matches. Commands are plugins
that require a user to specifically ask for helga to perform some action. For example,
``helga haiku`` or ``helga google something to search``. Matches are on the other hand are
intended to be autoresponders that give some extra meaning or context to what a user has said.
For example, if helga matches for a string "foo":

    <sduncan> i'm talking about foo in this message
    <helga> sduncan is talking about foo

For the sake of simplicity, there are two convenient decorators for authoring these types
of plugins (which is usually the case). For example:

.. code-block:: python

    from helga.plugins import command, match

    @command('foo', aliases=['foobar'], help="The foo command")
    def foo(client, channel, nick, message, cmd, args):
        # This is run on "helga foo" or "helga foobar"
        return u"Running the foo command"

    @match(r'bar')
    def bar(client, channel, nick, message, matches):
        # This will run whenever a user mentions the word 'bar'
        return u"{0} said bar!".format(nick)

You may notice in the above example that each decorated function accepts different arguments.
For commands, there are two additional arguments ``cmd`` and ``args``. The former is the parsed
command that was used to run the method (which could be "foo" in the above case, or the alias
"foobar"). The latter is a list of whitespace delimited strings that follow the parsed commend.
For example ``helga foo a b c`` would mean the args param would be ``['a', 'b', 'c']``.

For the match plugin, the single additional argument is ``matches`` which is for the most part,
the result of ``re.findall``. However, the ``@match`` decorator accepts a callable in place of
a regex string. This callable should accept one argument: the message being processed. It should
return a value that can be evaluated for truthiness and will be passed to the decorated function
as the ``matches`` parameter.

Preprocessors
+++++++++++++

Plugins can also be message preprocessors. These are callables that may perform some modification
on an incoming message prior to that message being delivered to any plugins. Preprocessors should
accept arguments (in order) for ``client``, ``channel``, ``nick``, and ``message`` and should
return a three-tuple consisting of (in order) ``channel``, ``nick``, and ``message``. To declare
a function as a preprocessor, a convenient decorator can be used:

.. code-block:: python

    from helga.plugins import preprocessor

    @preprocessor
    def blank_message(client, channel, nick, message):
        return channel, nick, u''

Complex plugins
+++++++++++++++

Some plugins do both matching and act as a command. For this reason, plugin decorators are chainable.
However, remember that different plugin types expect decorated functions to accept different arguments.
It is best to accept ``*args`` for these:

.. code-block:: python

    from helga.plugins import command, match, preprocessor

    @preprocessor
    @match(r'bar')
    @command('foo')
    def complex(client, channel, nick, message, *args):
        # len(args) == 0 for preprocessors
        # len(args) == 1 for matches
        # len(args) == 2 for commands

Plugin Priorities
+++++++++++++++++

You can control the priority in which a plugin is run. Note though, that preprocessors will always
run first. A priority value should be an integer value. There are no limits or bounds for this value,
but know that a higher value will mean a higher priority. If you are writing ``Plugin`` subclass
style plugins, you will need to set a ``priority`` attribute of your object. This is done automatically
if you call ``super(MyClass, self).__init__(priority=some_value)`` in your class's ``__init__``.

However, if you are using the preferred decorator style for writing plugins, you can supply a ``priority``
keyword argument to the decorator:

.. code-block:: python

    from helga import command, match, preprocessor

    @preprocessor(priority=10)
    def foo_preprocess(*args):
        pass

    @command('foo', priority=20)
    def foo_command(*args):
        pass

    @match(r'foo', priority=30)
    def foo_match(*args):
        pass

For convenience, there are constants that can be used for setting priorities:

- **PRIORITY_LOW** = 25
- **PRIORITY_NORMAL** = 50
- **PRIORITY_HIGH** = 75

Also, each decorator/plugin type has its own default value for priority:

- Preprocessors have default priority of ``PRIORITY_NORMAL``
- Commands have default priority of ``PRIORITY_NORMAL``
- Matches have default priority of ``PRIORITY_LOW``

Publishing plugins
++++++++++++++++++

Helga uses setuptools entry points for plugin loading. Once you've written a plugin you wish to use,
you will need to make sure your python package's setup.py contains an entry_point under the group
name ``helga_plugins``. For example:

.. code-block:: python

    entry_points = {
        'helga_plugins': [
            'plugin_name = mylib.mymodule:MyPluginClass',
        ],
    },

Note that if you are using decorated function for a plugin, you will want to specify the method name
for your entry point, i.e. ``mylib.mymodule:myfn``.


Webhooks
++++++++

As of helga version 1.3, there is an included plugin for exposing an HTTP server to support webhooks.
This might be useful if you need to have a public facing HTTP service that you would like to use to
perform some sort of announcement on a particular channel. This is also very extensible and should allow
you to create new webhooks in a very similar way plugins are created. This plugin is enabled by default
and requires two settings: ``WEBHOOKS_PORT`` and ``WEBHOOKS_CREDENTIALS``. The former is of course the
port on which to run this service. The latter should be a list of tuples in the form of (username, password).
These are used to perform HTTP basic authentication on any webhook that requires it.

Webhook plugins work by declaring routes. This will not only feel similar to helga's decorator style
plugins, but it will also feel very similar to anyone who has used something like Flask. There are two
primary decorators you will need to get started: ``route``, which declares a function as a route endpoint,
and ``authenticated``, which ensures that the route function cannot be called without proper HTTP basic
authentication. Both of these can be imported from ``helga.plugins.webhooks``. For example:

.. code-block:: python

    from helga.plugins.webhooks import authenticated, route

    @route(r'/foo/(?P<id>[0-9]+)')
    @authenticated
    def foo(request, irc_client, id):
        # This will require auth
        pass

    @route('/bar', methods=['POST'])
    def bar(request, irc_client):
        # This will not require auth, and will only accept POST
        pass

NOTE: For authenticated routes, you MUST specify ``@authenticated`` as the first decorator. This may be
changed in the future.

The route decorator accepts two arguments: 1) a path regular expression and 2) an optional list of
HTTP methods to accept. If you do not specify a list of HTTP methods, only GET requests will be served.
All regex paths must be named groups and they will be passed as keyword arguments.

To register a new webhook plugin, you must declare an entry_point much in the same way normal plugins
are done. However, the entry_point group name is ``helga_webhooks``. For example:

.. code-block:: python

    entry_points = {
        'helga_webhooks': [
            'name = mylib.mymodule:myhook',
        ],
    },

The webhook plugin itself has some commands for IRC interaction: start/stop to control the running HTTP
listener, and routes, which will show all the route paths and the HTTP methods they accept.


Third Party Plugins
+++++++++++++++++++

Here are some plugins that have been written that you can use:

+---------+------------------------------------------------------+-------------------------------------------------+
| Plugin  | Description                                          | Link                                            |
+=========+======================================================+=================================================+
| excuses | Generate a response from http://developerexcuses.com | https://github.com/alfredodeza/helga-excuses    |
+---------+------------------------------------------------------+-------------------------------------------------+
| haskell | Evaluate Haskell expressions.                        | https://github.com/carymrobbins/helga-haskell   |
+---------+------------------------------------------------------+-------------------------------------------------+
| isup    | Check downforeveryoneorjustme.com                    | https://github.com/shaunduncan/helga-isup       |
+---------+------------------------------------------------------+-------------------------------------------------+
| karma   | Dish out karma points to other people                | https://github.com/coddingtonbear/helga-karma   |
+---------+------------------------------------------------------+-------------------------------------------------+
| norris  | Generate Chuck Norris facts for users                | https://github.com/alfredodeza/helga-norris     |
+---------+------------------------------------------------------+-------------------------------------------------+
| updates | List and record IRC channel updates.                 | https://github.com/cobbdb/helga-contrib-updates |
+---------+------------------------------------------------------+-------------------------------------------------+
| zen     | The Zen of Python                                    | https://github.com/shaunduncan/helga-zen        |
+---------+------------------------------------------------------+-------------------------------------------------+

Written a plugin? Send a pull request to be listed in the above table!


Tests
-----

All tests are written to be run via ``tox``. To run the test suite, inside your virtualenv:

.. code-block:: bash

    $ cd src/helga
    $ tox

Contributing
------------

Contributions are welcomed, as well as any bug reports! Please note that any pull request will be denied
if tests run via tox do not pass

License
-------

Copyright (c) 2013 Shaun Duncan

Dual licensed under the `MIT`_ and `GPL`_ licenses.

.. _`GPL`: https://github.com/shaunduncan/helga/blob/master/LICENSE-GPL
.. _`MIT`: https://github.com/shaunduncan/helga/blob/master/LICENSE-MIT
