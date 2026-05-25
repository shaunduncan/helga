# Helga

Chat bot for Python 3.8+ built on Twisted. Supports IRC, XMPP, Slack, Discord.

## Entrypoints

- CLI: `helga.bin.helga:main` (console_script `helga`)
- Settings: `HELGA_SETTINGS` env var or `--settings` flag (module path or file path)
- Server type: `settings.SERVER['TYPE']` — `'irc'` (default), `'xmpp'`, `'slack'`

## Commands

```bash
# install dev
pip install -e '.[dev]'
pre-commit install

# lint / format / typecheck (run in this order)
ruff check helga
black --check helga
mypy helga

# auto-fix
ruff check --fix helga
black helga

# test
pytest                                              # all tests
pytest helga/tests/test_settings.py                 # single file
pytest helga/tests/test_settings.py::test_configure # single test

# full CI pipeline equivalent
ruff check helga && black --check helga && mypy helga && pytest
```

## Key quirks

- **`HELGA_SETTINGS` must be empty string** for tests (`HELGA_SETTINGS=''`), otherwise settings module override can break test isolation.
- **MongoDB** is optional for core operation but required by some features. Tests mock pymongo — no real DB needed.
- **Tox/CI** runs across Python 3.8–3.13 with a MongoDB service container.
- **Pre-commit** runs Black + Ruff on every commit (passes `--fix --exit-non-zero-on-fix` to ruff).
- **Coverage** is always on (pytest addopts includes `--cov=helga --cov-report=term-missing`).
- **`pyproject.toml`** is the primary config; `setup.py` is backward-compat only.

## Architecture

```
helga/
  bin/helga.py       # CLI entrypoint, reactor setup
  comm/              # protocol clients (base, irc, xmpp, slack)
  plugins/           # plugin framework (Registry, Plugin, Command, Match decorators)
  webhooks/          # HTTP webhook handlers
  tests/             # mirrors helga/ structure
  settings.py        # defaults + configure()
  db.py              # MongoDB connection (module-level connect())
  log.py             # logging utilities
```

- Plugins register via `helga_plugins` entry_points (setuptools) or decorators (`@command`, `@match`, `@preprocessor`).
- Plugin loading happens on the `started` signal.
- Built-in plugins: `help`, `manager`, `operator`, `ping`, `version`, `webhooks`.

## Docker

```bash
docker-compose up    # IRC server (localhost:6667) + MongoDB
```

## Release

- Bump version in `helga/__init__.py` and `pyproject.toml`
- Tag `vX.Y.Z` on GitHub; CI builds/publishes to PyPI and GHCR
