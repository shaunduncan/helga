CHANGELOG
=========

1.7.6
-----
- Added support for IRC NAMES with a signal callback: names_reply


1.7.2
-----
- Merged #147: Track /me messages sent over chat
- Merged #149: Allow "!plugins" with no argument to list known plugins
- Merged #151: Upgrade OpenSSL dependency

1.7.1
-----
- Fixed #145: XMPP client doesn't have operators attribute
- Added a simple version check plugin that responds with the current helga version


1.7.0
-----
- Fixed #118: Removed hash attribute of reminders and used the full ObjectId
- Fixed #136: improve plugin whitelist/blacklist functionality and clarity
- Fixed #142: Split out non-essential plugins into their own repos
    - Removed dubstep plugin. Now at https://github.com/shaunduncan/helga-dubstep (pypi helga-dubstep)
    - Removed facts plugin. Now at https://github.com/shaunduncan/helga-facts (pypi helga-facts)
    - Removed giphy plugin. Now at https://github.com/shaunduncan/helga-giphy (pypi helga-giphy)
    - Removed icanhazascii plugin. Now at https://github.com/shaunduncan/helga-icanhazascii (pypi helga-icanhazascii)
    - Removed jira plugin. Now at https://github.com/shaunduncan/helga-jira (pypi helga-jira)
    - Removed loljava plugin. Now at https://github.com/shaunduncan/helga-loljava (pypi helga-loljava)
    - Removed meant_to_say plugin. Now at https://github.com/shaunduncan/helga-meant-to-say (pypi helga-meant-to-say)
    - Removed no_more_olga plugin. Now at https://github.com/shaunduncan/helga-no-more-olga (pypi helga-no-more-olga)
    - Removed oneliner plugin. Now at https://github.com/shaunduncan/helga-oneliner (pypi helga-onliner)
    - Removed poems plugin. Now at https://github.com/shaunduncan/helga-poems (pypi helga-poems)
    - Removed reminders plugin. Now at https://github.com/shaunduncan/helga-reminders (pypi helga-reminders)
    - Removed reviewboard plugin. Now at https://github.com/shaunduncan/helga-reviewboard (pypi helga-reviewboard)
    - Removed stfu plugin. Now at https://github.com/shaunduncan/helga-stfu (pypi helga-stfu)
    - Removed wiki_whois plugin. Now at https://github.com/shaunduncan/helga-wiki-whois (pypi helga-wiki-whois)
- Added beta version of XMPP/HipChat support and updated documentation
- Added a simple ping command plugin that responds with 'pong'


1.6.8
-----
- Merge #141 - Unpin pytz to fix broken dependency
- Fix broken "at" reminder code with pytz update


1.6.7
-----
- Fixed #140 - Allow simple string channel names for CHANNELS setting
- Merged PR #138 - Fix shell oneliner response


1.6.6
-----
- Fixed #137 - Chicken/egg situation with @route in the same module as a command or match


1.6.5
-----
- Fixed #134 - Missing __init__.py in helga.bin causing console script issues


1.6.4
-----
- Fixed #133 - custom settings are not properly overriding client settings


1.6.3
-----
- Added full documentation and updated many docstrings.
- Removed package helga.plugins.core contents and placed in helga.plugins.__init__
- Updated setup.py to support pip >= 0.7
- Fixed #20 - Added case-insensitive command support.
- Fixed #131 - ResponseNotReady does not honor PLUGIN_FIRST_RESPONDER_ONLY = False


1.6.2
-----
- Fix UnicodeDecodeError for channel log web UI


1.6.1
-----
- Fix broken packaging that did not include channel log web UI mustache templates.


1.6.0
-----
- Added a new channel logger to log conversations to UTC dated text files. Also features a
  web UI for log browsing.
- Fixed #68 - Custom settings overrides can be supplied via command line argument --settings.
  The old env var is still supported. Either option can be an import string 'foo.bar.baz' or
  a path on the filesystem 'foo/bar/baz.py'
- Fixed #77 - Allow custom plugin priority weights to be set in settings overrides
- Fixed #83 - The JIRA plugin no longer uses BeautifulSoup as a fallback
- Fixed #107 - Set erroneousNickFallback for default IRC client
- Fixed #111 - Better README docs on SERVER settings
- Fixed #120 - Operator plugin doesn't format responses properly
- Fixed #123 - Changed PyPI classifier to Production/Stable
- Fixed #126 - JIRA plugin exception when JIRA_PATTERNS is empty
- Fixed #127 - Allow optional setting to use shlex for comman arg string parsing instead of
  naive whitespace splitting (see README for COMMAND_ARGS_SHLEX). This can also be a command
  decorator argument like @command('foo', shlex=True).


1.5.2
-----
- Merged PR #119 - Adding replace command for facts plugin
- Merged PR #117 - Fix oneliner regex to not be noisy for gfycat links


1.5.1
-----
- Added AUTO_RECONNECT support for failed connections (in addition to lost connections)
- Added AUTO_RECONNECT_DELAY to have a sensible wait time before connect retries


1.5.0
-----
- Fix The Unicode Problem(TM) (Issue 86)
- Vastly improved test suite. Now with 100% test coverage


1.4.6
-----
- Fixed regex bug in command parsing that looks for a space after a command/alias


1.4.5
-----
- Fixed a bug where the WebHook root object doesn't get the current IRC client
  on signon. (Issue #89)


1.4.4
-----
- Signals are now sent when a user joins or leaves a channel. Sending args
  (client, nick, channel)


1.4.3
-----
- Changed markdown documents to reStructuredText


1.4.2
-----
- Fix a quirk in command alias ordering where shorter commands would override
  the longer variants (i.e. 't' vs 'thanks')


1.4.1
-----
- Minor adjustment to operator plugin docstring


1.4.0
-----
- Merged pull requests #59 and #62
- Changed license from MIT to dual MIT/GPLv3
- Switched to semantic versioning


1.3
---
- Refactored simple announcement service into an extensible webhook plugin system


1.2
---
- Added a very simple announcement HTTP service


1.1
---
- Included ability for operators to reload installed plugins without restarting
- Haiku/Tanka tweets now run via ``reactor.callLater``
- Any plugin that raises ``ResponseNotReady`` when helga is set to allow first
  response only will prevent other plugins from running


1.0
---
- Completely refactored the internal plugin API to be simpler and easier to use
- All plugins use setuptools entry_points now
