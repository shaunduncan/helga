import sys

from twisted.internet import reactor

from helga import settings
from helga.db import db
from helga.factory import HelgaFactory
from helga.log import setup_logger


logger = setup_logger(__name__)


_help = """
Usage: helga option

Avalable options:
help        Show this message
start       Start the helga bot (CTRL-C to stop)
loaddata    Load JSON directly into MongoDB
"""


def start():
    factory = HelgaFactory()
    reactor.connectTCP(settings.SERVER['HOST'],
                       settings.SERVER['PORT'],
                       factory)
    reactor.run()


def run():
    args = sys.argv[1:]
    if len(args) == 0 or args[0] == 'help':
        start()
