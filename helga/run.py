import sys

from twisted.internet import reactor, ssl

from helga import settings
from helga.factory import HelgaFactory
from helga.log import setup_logger


logger = setup_logger(__name__)


_help = """
Usage: helga <option>

Avalable options:
help        Show this message
start       Start the helga bot (CTRL-C to stop)
"""


def start():
    factory = HelgaFactory()
    if settings.SERVER.get('SSL', False):
        reactor.connectSSL(settings.SERVER['HOST'],
                           settings.SERVER['PORT'],
                           factory,
                           ssl.ClientContextFactory())
    else:
        reactor.connectTCP(settings.SERVER['HOST'],
                           settings.SERVER['PORT'],
                           factory)
    reactor.run()


def run():
    args = sys.argv[1:]
    if len(args) == 0 or args[0] == 'help':
        start()
