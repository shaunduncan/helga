from twisted.internet import protocol, reactor

from helga import settings
from helga.client import HelgaClient
from helga.log import setup_logger


logger = setup_logger(__name__)


class HelgaFactory(protocol.ClientFactory):

    def buildProtocol(self, address):
        logger.debug('Constructing Helga protocol')
        helga = HelgaClient()
        helga.factory = self
        return helga

    def clientConnectionLost(self, connector, reason):
        logger.info('Connection to server lost: %s' % reason)
        raise reason

        # FIXME: Max retries
        if getattr(settings, 'AUTO_RECONNECT', True):
            connector.connect()

    def clientConnectionFailed(self, connector, reason):
        logger.warning('Connection to server failed: %s' % reason)
        reactor.stop()
