import sys

import smokesignal

from twisted.internet import reactor, ssl

from helga import comm, settings


_help = """
Usage: helga <option>

Avalable options:
help        Show this message
start       Start the helga bot (CTRL-C to stop)
"""


def start():
    smokesignal.emit('started')

    factory = comm.Factory()
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
