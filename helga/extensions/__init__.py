from helga import settings
from helga.extensions.base import (HelgaExtension,
                                   CommandExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class ExtensionRegistry(object):

    def __init__(self, bot, load=True):
        self.ext = set()
        self.imported = set()
        self.bot = bot

        if load:
            self.load()

    def _make_import_args(self, path):
        return path, {}, {}, [path.split('.')[-1]]

    def _get_possible_extensions(self, mod):
        return filter(lambda x: not x.startswith('__'), dir(mod))

    def load_module_members(self, module):
        # See if there are any HelgaExtensions
        for member in self._get_possible_extensions(module):
            try:
                cls = getattr(module, member)
                if issubclass(cls, HelgaExtension) and cls != HelgaExtension and cls not in self.imported:
                    self.ext.add(cls(bot=self.bot))
                    self.imported.add(cls)
            except TypeError:
                continue

    def load(self):
        for path in getattr(settings, 'EXTENSIONS', []):
            logger.debug('Loading extension extension %s' % path)

            try:
                module = __import__(*self._make_import_args(path))
            except ImportError:
                logger.warning('Cannot import extension %s' % path)
                continue

            self.load_module_members(module)

    def _iter_call_cls(self, fn_attr, nick, channel, message, is_public, cls=None, invert=False):
        for ext in self.ext:
            if invert:
                should_skip = cls and isinstance(ext, cls)
            else:
                should_skip = cls and not isinstance(ext, cls)

            if should_skip:
                continue

            try:
                resp = getattr(ext, fn_attr)(nick, channel, message, is_public)
            except:
                logger.exception('Unexpected failure. Skipping extension')
                continue

            if isinstance(resp, tuple):
                resp, message = resp

            if resp:
                return resp, message

        return None, message

    def _iter_call(self, fn_attr, nick, channel, message, is_public):
        # This is kind of crappy, but commands should go first
        args = [fn_attr, nick, channel, message, is_public]
        resp, message = self._iter_call_cls(*args, cls=CommandExtension)

        if resp:
            return resp, message
        else:
            args[3] = message

        return self._iter_call_cls(*args, cls=CommandExtension, invert=True)

    def on(self, event, *args, **kwargs):
        # Eww, just eww
        for ext in self.ext:
            ext.on(event, *args, **kwargs)

    def pre_dispatch(self, nick, channel, message, is_public):
        return self._iter_call('pre_dispatch', nick, channel, message, is_public)

    def dispatch(self, nick, channel, message, is_public):
        return self._iter_call('dispatch', nick, channel, message, is_public)[0]
