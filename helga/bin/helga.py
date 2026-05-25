import argparse
import os

import smokesignal
from autobahn.twisted.websocket import connectWS
from twisted.internet import reactor, ssl

from helga import settings


def _get_backend(name):  # pragma: no cover
    name = name.lower()
    module = __import__("helga.comm", globals(), locals(), [name], 0)
    return getattr(module, name)


def run():
    """
    Run the helga process
    """
    backend = _get_backend(settings.SERVER.get("TYPE", "irc"))
    smokesignal.emit("started")

    factory = backend.Factory()

    server_type = settings.SERVER.get("TYPE", "irc")

    if server_type == "slack":
        connectWS(factory=factory)
        reactor.run()
    elif server_type == "discord":
        # Discord uses its own event loop, not Twisted's reactor
        factory.connect()
        reactor.run()
    elif settings.SERVER.get("SSL", False):
        reactor.connectSSL(
            settings.SERVER["HOST"], settings.SERVER["PORT"], factory, ssl.ClientContextFactory()
        )
        reactor.run()
    else:
        reactor.connectTCP(settings.SERVER["HOST"], settings.SERVER["PORT"], factory)
        reactor.run()


def main():
    """
    Main entry point for the helga console script
    """
    parser = argparse.ArgumentParser(description="The helga IRC bot")
    parser.add_argument(
        "--settings",
        help=(
            "Custom helga settings overrides. This should be an importable python module "
            'like "foo.bar.baz" or a path to a settings file like "path/to/settings.py". '
            "This can also be set via the HELGA_SETTINGS environment variable, however "
            "this flag takes precedence."
        ),
    )
    args = parser.parse_args()

    settings_file = os.environ.get("HELGA_SETTINGS", "")

    if args.settings:
        settings_file = args.settings

    settings.configure(settings_file)
    run()
