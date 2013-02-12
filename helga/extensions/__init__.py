import logging

from helga import settings
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(logging.getLogger(__name__))


class ExtensionRegistry(object):

    def __init__(self):
        self._ext = set()

    def ensure(self):
        for path in getattr(settings, 'EXTENSIONS', []):
            try:
                mod = __import__(path, {}, {}, [path.split('.')[-1]])
            except ImportError:
                logger.warning('Cannot import extension %s' % path)
                continue

            # See if there are any HelgaExtensions
            for member in filter(lambda x: not x.startswith('__'), dir(mod)):
                try:
                    cls = getattr(mod, member)
                    if issubclass(cls, HelgaExtension) and cls != HelgaExtension:
                        self._ext.add(cls())
                except TypeError:
                    continue

    def dispatch(self, bot, nick, channel, message, is_public):
        responses = []

        for ext in self._ext:
            responses.append(ext.dispatch(bot, nick, channel, message, is_public))

        return responses


extensions = ExtensionRegistry()
