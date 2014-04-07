CHANGELOG
=========

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
