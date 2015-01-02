 _builtin:

Builtin Features
================
Helga comes with many builtin plugins, webhooks, and features.


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


.. _builtin.plugins.dubstep:

dubstep
^^^^^^^
A match plugin that will respond with vaiable length 'wubwubwub' when someone mentions the word 'dubstep'.


.. _builtin.plugins.facts:

facts
^^^^^
.. important::

    This plugin requires database access

A match plugin that can be used to store responses that can be returned from a question. For example::

    <sduncan> foo is bar
    <sduncan> foo?
    <helga> foo is bar (sduncan on 12/01/2014 08:15)
    <sduncan> bar baz are qux
    <sduncan> bar baz?
    <helga> bar baz is qux (sduncan on 12/01/2014 08:15)

Facts are queried using the form ``fact?`` and are stored automatically using the form
``fact (is|are) term``. In this simple fact storing form, facts are saved with the nick of the user
that saying it and the timestamp at which it was said. Facts can also be stored as a reply only
without a nick or timestamp by using the token '<reply>'::

    <sduncan> foo is <reply> bar
    <sduncan> foo?
    <helga> bar

Optionally, if the setting ``FACTS_REQUIRE_NICKNAME`` is set to True, the bot's nick will be required
to show a stored fact (see :ref:`config.default.plugins.facts`)::

    <sduncan> foo is <reply> bar
    <sduncan> foo?
    <sduncan> helga foo?
    <helga> bar


.. _builtin.plugins.giphy:

giphy
^^^^^
A command plugin to search `giphy`_ for an anmiated gif. Usage::

    helga (gif|gifme) <search term>

An optional setting ``GIPHY_API_KEY`` can be set for API access, but will default to giphy's public
API key (see :ref:`config.default.plugins.giphy`).


.. _builtin.plugins.help:

help
^^^^
A command plugin to show help strings for any installed command plugin. Usage::

    helga (help|halp) [<plugin>]

With no arguments, all command plugin help strings are returned to the requesting user in a private message.


.. _builtin.plugins.icanhazascii:

icanhazascii
^^^^^^^^^^^^
A match plugin that will show ASCII art for certain keywords. This plugin is rate-limited at a
maximum of one response per channel every 30 seconds. ASCII art includes:

poniez::

             .,,.
          ,;;*;;;;,
         .-'``;-');;.
        /'  .-.  /*;;
      .'    \d    \;;               .;;;,
     | o      `    \;             ,;*;;;*;,
     \__, _.__,'   \_.-') __)--.;;;;;*;;;;,
      `""`;;;\       /-')_) __)  `\' ';;;;;;
         ;*;;;        -') `)_)  |\ |  ;;;;*;
         ;;;;|        `---`    O | | ;;*;;;
         *;*;\|                 O  / ;;;;;*
        ;;;;;/|    .-------\      / ;*;;;;;
       ;;;*;/ \    |        '.   (`. ;;;*;;;
       ;;;;;'. ;   |          )   \ | ;;;;;;
       ,;*;;;;\/   |.        /   /` | ';;;*;
        ;;;;;;/    |/       /   /__/   ';;;
        '*;;*/     |       /    |      ;*;
             `""""`        `""""`     ;'

puppiez::

                               _
                            ,:'/   _..._
                           // ( `""-.._.'
                           \| /    0\___
                           |            4
                           |            /
                           \_       .--'
                           (_'---'`)
                           / `'---`()
                         ,'        |
         ,            .'`          |
         )\       _.-'             ;
        / |    .'`   _            /
      /` /   .'       '.        , |
     /  /   /           \   ;   | |
     |  \  |            |  .|   | |
      \  `"|           /.-' |   | |
       '-..-\       _.;.._  |   |.;-.
             \    <`.._  )) |  .;-. ))
             (__.  `  ))-'  \_    ))'
                 `'--"`       `"""`

dolphinz::

                                        __     HAI!
                                    _.-~  )
                         _..--~~~~,'   ,-/     _
                      .-'. . . .'   ,-','    ,' )
                    ,'. . . _   ,--~,-'__..-'  ,'
                  ,'. . .  (@)' ---~~~~      ,'
                 /. . . . '~~             ,-'
                /. . . . .             ,-'
               ; . . . .  - .        ,'
              : . . . .       _     /
             . . . . .          `-.:
            . . . ./  - .          )
           .  . . |  _____..---.._/
     ~---~~~~----~~~~             ~~~~~~~~~~~~~~~

kittiez::

       _             _
      | '-.       .-' |
       \'-.'-"""-'.-'/    _
        |= _:'.':_ =|    /:`)
        \ <6>   <6> /   /  /
        |=   |_|   =|   |:'\
        >\:.  "  .:/<    ) .|
         /'-._^_.-'\    /.:/
        /::.     .::\  /' /
      .| '::.  .::'  |;.:/
     /`\:.         .:/`\(
    |:. | ':.   .:' | .:|
    | ` |:.;     ;.:| ` |
     \:.|  |:. .:|  |.:/
      \ |:.|     |.:| /
      /'|  |\   /|  |`\
     (,,/:.|.-'-.|.:\,,)
       (,,,/     \,,,)""",

batsignal::

           _==/          i     i          \==_
         /XX/            |\___/|            \XX\
       /XXXX\            |XXXXX|            /XXXX\
      |XXXXXX\_         _XXXXXXX_         _/XXXXXX|
     XXXXXXXXXXXxxxxxxxXXXXXXXXXXXxxxxxxxXXXXXXXXXXX
    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
     XXXXXX/^^^^"\XXXXXXXXXXXXXXXXXXXXX/^^^^^\XXXXXX
      |XXX|       \XXX/^^\XXXXX/^^\XXX/       |XXX|
        \XX\       \X/    \XXX/    \X/       /XX/
           "\       "      \X/      "      /"

.. note::

    Future development of this plugin will be maintained elsewhere. It will be removed as a builtin
    plugin in a future version.


.. _builtin.plugins.jira:

jira
^^^^
.. important::

    This plugin requires database access

A configurable match plugin for providing links and/or descriptions of JIRA tickets. For example::

    <sduncan> can you look at API-123
    <helga> sduncan might be talking about JIRA ticket http://example.com/API-123

Regular expressions for this plugin are stored as the project key without any numbers. So in the
example above, the regular expression for 'API-123' is stored as 'API'. This plugin also responds
with multiple tickets should they be found::

    <sduncan> i'm working on API-123 and API-456
    <helga> sduncan might be talking about JIRA ticket http://example.com/API-123, http://example.com/API-456

Optionally, this plugin can use JIRA's REST API in order to show full ticket descriptions if the
setting ``JIRA_REST_API`` is set and ``JIRA_SHOW_FULL_DESCRIPTIONS`` is set to True::

    <sduncan> can you look at API-123
    <helga> [API-123] Make a new version of the API

For all configuration options, see :ref:`config.default.plugins.jira`. This plugin also includes
a command for adding or removing JIRA ticket patterns. Usage::

    helga jira (add_re|remove_re) <pattern>

For example::

    <sduncan> !jira add_re API
    <sduncan> API-123
    <helga> sduncan might be talking about JIRA ticket http://example.com/API-123
    <sduncan> !jira remove_re API
    <sduncan> API-123


.. _builtin.plugins.loljava:

loljava
^^^^^^^
A match plugin that will respond with a silly generated Java class name when someone mentions
the word 'java'.


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


.. _builtin.plugins.meant_to_say:

meant_to_say
^^^^^^^^^^^^
A match plugin for users to indicate that they meant to say something differnent from what they did.
This plugin will match replacement syntax like 's/foo/bar/', much like using sed. For example::

    <sduncan> foo is bar
    <sduncan> s/foo/bar/
    <helga> sduncan meant to say: bar is bar


.. _builtin.plugins.no_more_olga:

no_more_olga
^^^^^^^^^^^^
A match plugin that aided in the early days of helga when the bot `olga`_ was still in use. Since helga
started as a python fork of olga, many users were used to asking olga for certain actions. This would
respond with a reminder that they should use helga instead.

.. note::

    Future development of this plugin will be maintained elsewhere. It will be removed as a builtin
    plugin in a future version.


.. _builtin.plugins.oneliner:

oneliner
^^^^^^^^
A match plugin with a large amount of canned responses for a variety of regular expressions. For the
full list, see the `source code <https://github.com/shaunduncan/helga/blob/master/helga/plugins/oneliner.py>`
for this plugin.


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


.. _builtin.plugins.poems:

poems
^^^^^
.. important::

    This plugin requires database access

A command plugin to generate either haiku or tanka poems. All five or seven syllable lines are user
generated and stored using this plugin. Usage::

    helga (haiku|tanka) [blame|tweet|about <term>|by <nick>|(add|add_use|use|remove|claim) (fives|sevens) (INPUT ...)].

Without any arguments ``helga haiku`` or ``helga tanka`` will produce a randomly generated haiku or
tanka from stored five or seven syllable lines respectively. Each subcommand acts as follows:

``blame``
    Get a list of the nicks of the users that authored the lines of a generated haiku

``about <term>``
    Generate a haiku or tanka using a given term. This term supports any valid regular expression.
    For example, ``!haiku about foo`` will search for lines containing 'foo', but ``!haiku about foo$``
    will only return lines that end with foo

``by <nick>``
    Generate a haiku or tanka with lines by the given nick. If not enough lines exist for this nick,
    then lines are selected at random

``add (fives|sevens) (INPUT ...)``
    Add a five or seven syllable line to the database but do not generate a poem

``add_use (fives|sevens) (INPUT ...)``
    Add a five or seven syllable line to the database and then generate and return a poem containing
    that line

``use (fives|sevens) (INPUT ...)``
    Generate a poem containing the given five or seven syllable line, but do not store it for future poems

``claim (fives|sevens) (INPUT ...)``
    Allows the requesting user to claim authorship of a given five or seven syllable line

A bit of an undocumented feature, but poems can be tweeted to some Twitter account. For example, generating
a poem with ``!haiku`` followed by ``!haiku tweet``. This requires some additional settings:

* ``TWITTER_CONSUMER_KEY``
* ``TWITTER_CONSUMER_SECRET``
* ``TWITTER_OAUTH_TOKEN``
* ``TWITTER_OAUTH_TOKEN_SECRET``
* ``TWITTER_USERNAME``


.. _builtin.plugins.reminders:

reminders
^^^^^^^^^
.. important::

    This plugin requires database access

A command plugin for scheduling one time or recurring reminders in IRC. Usage::

    helga (in ##(m|h|d) [on <channel>] <message>|at <HH>:<MM> [<timezone>] [on <channel>] <message> [repeat <days_of_week>]|reminders list [channel]|reminders delete <hash>)

Each reminder setting command acts as follows:

``in ##(m|h|d) [on <channel>] <message>``
    Schedule a message to appear in some number of minutes, hours, or days on the current channel.
    Optionally, ``on <channel>`` will set this reminder to occur on the specified channel. This is useful
    for setting channel reminders via a private message. For example::

        <sduncan> !in 8h on #work QUITTING TIME!

``at <HH>:<MM> [<timezone>] [on <channel>] <message> [repeat <days_of_week>]``
    Schedule a message to appear at a specific time in the future. ``on <channel>`` will set this reminder
    to occur on the specified channel, which is useful for setting channel reminders via a private message.
    If not specified, the default timezone is assumed to be UTC, otherwise a timezone such as
    'US/Eastern' that can be recognized by pytz can be specified. Times must be in 24h clock format.
    For example::

        <sduncan> !at 17:00 US/Eastern on #work QUITTING TIME!

    You can also set these reminders to occur at repeating intervals in the future by specifying ``repeat``
    followed by a string of days of the week. For example::

        <sduncan> !at 17:00 US/Eastern on #work QUITTING TIME! repeat MTuWThF

    Valid days of the week are:

    * ``Su``: Sunday
    * ``M``: Monday
    * ``Tu``: Tuesday
    * ``W``: Wednesday
    * ``Th``: Thursday
    * ``F``: Friday
    * ``Sa``: Saturday

``reminders list [channel]``
    List all of the reminders set to occur on the current channel. Specifying a channel name will list
    all the reminders set to occur on that channel.

``reminders delete <hash>``
    Delete a stored reminder with the given hash. Reminder hashes can be obtained using the
    ``reminders list`` command.


.. _builtin.plugins.reviewboard:

reviewboard
^^^^^^^^^^^
A match plugin for expanding shortcodes for code reviews on ReviewBoard. This matches the pattern
``cr(\d+)`` and requires configuring the setting ``REVIEWBOARD_URL`` (see
:ref:`config.default.plugins.reviewboard`). For example::

    <sduncan> can someone look at cr1234
    <helga> sduncan might be talking about codereview: http://example.com/r/1234

This match plugin will also show links for any code review match it finds::

    <sduncan> can someone look at cr1234 and cr456
    <helga> sduncan might be talking about codereview: http://example.com/r/1234, http://example.com/r/456


.. _builtin.plugins.stfu:

stfu
^^^^
A command and preprocessor to prevent any plugins from processing messages. This is useful if the bot
is being noisy on a channel and you wish to silence it. Usage::

    helga (stfu [for <minutes>]|speak)

Without any arguments, ``stfu`` will silence helga indefinitely. Otherwise, you can specify a number
of minutes for helga to be silent::

    <sduncan> !stfu for 5
    <helga> Ok I'll be back in 5 minutes

If the bot is currently silenced, you can unsilence it::

    <sduncan> !speak
    <helga> speaking again


.. _builtin.plugins.webhooks:

webhooks
^^^^^^^^
A special type of command plugin that enables webhook support (see :ref:`webhooks`). This command
is more of a high-level manager of the webhook system. Usage::

    helga webhooks (start|stop|routes)

Both ``start`` and ``stop`` are privileged actions and can start and stop the HTTP listener for
webhooks respectively. To use them, a user must be configured as an operator. The ``routes``
subcommand will list all of the URL routes known to the webhook listener.


.. _builtin.plugins.wiki_whois:

wiki_whois
^^^^^^^^^^
A command plugin to generate a confluence-type URL for a user, assuming that the nick given
is a valid confluence user. If given a nick 'foo', the end result this command produces is
something like ``http://example.com/~foo``. Usage::

    helga (showme|whois|whothehellis) <nick>

This requires a setting ``WIKI_URL`` (see :ref:`config.default.plugins.wiki_whois`).

.. note::

    Future development of this plugin will be maintained elsewhere. It will be removed as a builtin
    plugin in a future version.


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
disabled via the setting :data:`~helga.settins.CHANNEL_LOGGING`.

Channel logs are kept in UTC time and stored in dated logfiles that are rotated automatically. These
log files are written to disk in a configurable location indicated by :data:`~helga.settings.CHANNEL_LOGGING_DIR`
and are organized by channel name. For example, message that occurred on Dec 31 2014 on channel #foo
would be written to a file ``/path/to/logs/#foo/2014-12-31.txt``

The channel logger also includes a web frontend for browsing any logs on disk, documented as the builtin
webhook :ref:`builtin.webhooks.logger`.

.. note::

    Non-public channels (i.e. those not beginning with a '#') will be ignored by helga's channel
    logger. No conversations via private messages will be logged.


.. _`olga`: https://github.com/thepeopleseason/olga
