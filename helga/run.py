import logging

from twisted.internet import reactor

from helga import settings
from helga.factory import HelgaFactory
from helga.log import setup_logger


logger = setup_logger(logging.getLogger(__name__))


def runbot():
    factory = HelgaFactory()
    reactor.connectTCP(settings.SERVER['HOST'],
                       settings.SERVER['PORT'],
                       factory)
    reactor.run()
