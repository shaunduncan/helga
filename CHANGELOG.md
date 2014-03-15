# CHANGELOG

## 1.3

- Refactored simple announcement service into an extensible webhook plugin system

## 1.2

- Added a very simple announcement HTTP service

## 1.1

- Included ability for operators to reload installed plugins without restarting
- Haiku/Tanka tweets now run via ``reactor.callLater``
- Any plugin that raises ``ResponseNotReady`` when helga is set to allow first
  response only will prevent other plugins from running

## 1.0

- Completely refactored the internal plugin API to be simpler and easier to use
- All plugins use setuptools entry_points now
