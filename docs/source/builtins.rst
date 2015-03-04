 _builtin:


Builtin Features
================
Helga comes with many builtin plugins, webhooks, and features.


.. _builtin.supported_backends:

Supported Backends
------------------

As of version 1.7.0, helga supports IRC, XMPP, and HipChat out of the box. Note, however, that
helga originally started as an IRC bot, so much of the terminology will reflect that. The current
status of XMPP and HipChat support is very limited and somewhat beta. In the future, helga may
have a much more robust and pluggable backend system to allow connections to any number of chat
services.

The default configuration assumes that you wish to connect to an IRC server. However, if you wish
to connect to an XMPP or HipChat server, see :ref:`config.xmpp`.


.. _builtin.plugins:

Builtin Plugins
---------------
Helga comes with several builtin plugins. Generally speaking, it is better to have independently maintained
plugins rather than modifying helga core. In fact, many of the plugins listed here may be retired as
core plugins and moved to externally maintained locations. This is mainly due to the fact that some are
either not useful as core plugins or would require more maintenance for helga core than should be needed.

.. important::

    Some builtin plugins may be deprecated and removed in a future version of helga. They will be
    moved and maintained elsewhere as independent plugins.


.. _builtin.plugins.help:

help
^^^^
A command plugin to show help strings for any installed command plugin. Usage::

    helga (help|halp) [<plugin>]

With no arguments, all command plugin help strings are returned to the requesting user in a private message.


.. _builtin.plugins.manager:

manager
^^^^^^^
.. important::

    This plugin requires database access for some features

A command plugin that acts as an IRC-based plugin manager. Usage::

    helga plugins (list|(enable|disable) (<name> ...))

The 'list' subcommand will list out both enabled and disabled plugins for the current channel. For example::

    <sduncan> !plugins list
    <helga> Enabled plugins: foo, bar
    <helga> Disabled plugins: baz

Both enable and disable will respectively move a plugin between enabled and disabled status
on the current channel. If a database connection is configured, both enable and disable will record
plugins as either automatically enabled for the current channel or not. For example::

    <sduncan> !plugins enable baz
    <sduncan> !plugins list
    <helga> Enabled plugins: foo, bar, baz
    <sduncan> !plugins disable baz
    <helga> Enabled plugins: foo, bar
    <helga> Disabled plugins: baz


.. _builtin.plugins.operator:

operator
^^^^^^^^
.. important::

    This plugin requires database access for some features

A command plugin that exposes some capabilities exclusively for helga operators. Operators are nicks
with elevated privileges configured via the ``OPERATORS`` setting (see :ref:`helga.settings.core`).
Usage::

    helga (operator|oper|op) (reload <plugin>|(join|leave|autojoin (add|remove)) <channel>).

Each subcommand acts as follows:

``reload <plugin>``
    Experimental. Given a plugin name, perform a call to the python builtin ``reload()`` of the
    loaded module. Useful for seeing plugin code changes without restarting the process.

``(join|leave) <channel>``
    Join or leave a specified channel

``autojoin (add|remove) <channel>``
    Add or remove a channel from a set of autojoin channels. This features requries database access.


.. _builtin.plugins.ping:

ping
^^^^
A simple command plugin to ping the bot, which will always respond with 'pong'. Usage::

    helga ping


.. _builtin.plugins.webhooks:

webhooks
^^^^^^^^
A special type of command plugin that enables webhook support (see :ref:`webhooks`). This command
is more of a high-level manager of the webhook system. Usage::

    helga webhooks (start|stop|routes)

Both ``start`` and ``stop`` are privileged actions and can start and stop the HTTP listener for
webhooks respectively. To use them, a user must be configured as an operator. The ``routes``
subcommand will list all of the URL routes known to the webhook listener.


.. _builtin.webhooks:

Builtin Webhooks
----------------
Helga also includes some builtin webhooks for use out of the box.


.. _builtin.webhooks.announcements:

announcements
^^^^^^^^^^^^^
The announcements webhook exposes a single HTTP endpoint for allowing the ability to
post a message in an IRC channel via an HTTP request. This webhook **only** supports
POST requests and requires HTTP basic authentication (see :ref:`webhooks.authentication`).
Requests must be made to a URL path ``/announce/<channel>`` such as ``/announce/bots``
and made with a POST parameter ``message`` containing the IRC message contents. The
endpoint will respond with 'Message Sent' on a successful message send.


.. _builtin.webhooks.logger:

logger
^^^^^^
The logger webhook is a browsable web frontend for helga's builtin channel logger (see
:ref:`builtin.channel_logging`). This webhook is enabled by default but requires that channel
logging is enabled for it to be of any use. Logs are shown in a dated order, grouped by
channel.

Without any configuration, this web frontend will allow browsing all channels in which the
bot resides or has resided. This behavior can be changed with the setting
:data:`~helga.settings.CHANNEL_LOGGING_HIDE_CHANNELS` which should be a list of channel names
that should be hidden from the browsable web UI. NOTE: they can still be accessed directly.

This webhook exposes a root ``/logger`` URL endpoint that serves as a channel listing. The
webhook will support any url of the form ``/logger/<channel>/YYYY-MM-DD`` such as
``/logger/foo/2014-12-31``.


.. _builtin.channel_logging:

Channel Logging
---------------
As of the 1.6 release, helga includes support for a simple channel logger, which may be useful for
those wanting to helga to, in addition to any installed plugins, monitor and save conversations that
occur on any channel in which the bot resides. This is a helga core feature and not managed by a plugin,
mostly to ensure that channel logging *always* happens with some level of confidence that no
preprocess plugins have modified the message. Channel logging feature can be either enabled or
disabled via the setting :data:`~helga.settings.CHANNEL_LOGGING`.

Channel logs are kept in UTC time and stored in dated logfiles that are rotated automatically. These
log files are written to disk in a configurable location indicated by :data:`~helga.settings.CHANNEL_LOGGING_DIR`
and are organized by channel name. For example, message that occurred on Dec 31 2014 on channel #foo
would be written to a file ``/path/to/logs/#foo/2014-12-31.txt``

The channel logger also includes a web frontend for browsing any logs on disk, documented as the builtin
webhook :ref:`builtin.webhooks.logger`.

.. note::

    Non-public channels (i.e. those not beginning with a '#') will be ignored by helga's channel
    logger. No conversations via private messages will be logged.
