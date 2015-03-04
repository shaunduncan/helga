.. _api:

API Documentation
=================

:mod:`helga.comm.irc`
---------------------
.. automodule:: helga.comm.irc
    :synopsis: Twisted protocol and communication implementations for IRC
    :members:

:mod:`helga.comm.xmpp`
----------------------
.. automodule:: helga.comm.xmpp
    :synopsis: Twisted protocol and communication implementations for XMPP/HipChat
    :members:


:mod:`helga.db`
---------------
.. automodule:: helga.db
    :synopsis: pymongo connection objects and utilities
    :members:


:mod:`helga.log`
----------------
.. automodule:: helga.log
    :synopsis: Logging utilities for helga
    :members:


:mod:`helga.plugins`
--------------------
.. automodule:: helga.plugins
    :synopsis: Core plugin library
    :members:

    .. attribute:: registry

        A singleton instance of :class:`helga.plugins.Registry`


:mod:`helga.plugins.webhooks`
-----------------------------
.. automodule:: helga.plugins.webhooks
    :synopsis: Webhook HTTP server plugin and core webhook API
    :members:


:mod:`helga.settings`
---------------------
.. automodule:: helga.settings
    :synopsis: Default settings and configuration utilities
    :members: configure


    .. _helga.settings.chat:

    Chat Settings
    """""""""""""
    Settings that pertain to how helga operates with and connects to a chat server

    .. autodata:: NICK
    .. autodata:: CHANNELS
    .. autodata:: SERVER
    .. autodata:: AUTO_RECONNECT
    .. autodata:: AUTO_RECONNECT_DELAY
    .. autodata:: RATE_LIMIT


    .. _helga.settings.core:

    Core Settings
    """""""""""""
    Settings that pertain to core helga features.

    .. autodata:: OPERATORS
    .. autodata:: DATABASE


    .. _helga.settings.logging:

    Log Settings
    """"""""""""
    .. autodata:: LOG_LEVEL
    .. autodata:: LOG_FILE
    .. autodata:: LOG_FORMAT


    .. _helga.settings.channel_logging:

    Channel Log Settings
    """"""""""""""""""""
    See :ref:`builtin.channel_logging`

    .. autodata:: CHANNEL_LOGGING
    .. autodata:: CHANNEL_LOGGING_DIR
    .. autodata:: CHANNEL_LOGGING_HIDE_CHANNELS


    .. _helga.settings.plugins_and_webhooks:

    Plugin and Webhook Settings
    """""""""""""""""""""""""""
    Settings that control plugin and/or webhook behaviors. See :ref:`plugins` or :ref:`webhooks`

    .. autodata:: ENABLED_PLUGINS
    .. autodata:: DISABLED_PLUGINS
    .. autodata:: DEFAULT_CHANNEL_PLUGINS
    .. autodata:: ENABLED_WEBHOOKS
    .. autodata:: DISABLED_WEBHOOKS
    .. autodata:: PLUGIN_PRIORITY_LOW
    .. autodata:: PLUGIN_PRIORITY_NORMAL
    .. autodata:: PLUGIN_PRIORITY_HIGH
    .. autodata:: PLUGIN_FIRST_RESPONDER_ONLY
    .. autodata:: COMMAND_PREFIX_BOTNICK
    .. autodata:: COMMAND_PREFIX_CHAR
    .. autodata:: COMMAND_ARGS_SHLEX
    .. autodata:: WEBHOOKS_PORT
    .. autodata:: WEBHOOKS_CREDENTIALS


:mod:`helga.util.encodings`
---------------------------
.. automodule:: helga.util.encodings
    :synopsis: Utilities for working with unicode and/or byte strings
    :members:
