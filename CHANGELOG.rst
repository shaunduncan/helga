CHANGELOG
=========


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
