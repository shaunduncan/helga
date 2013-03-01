from helga import settings
from helga.extensions.base import (HelgaExtension,
                                   CommandExtension)
from helga.extensions.core import (ControlExtension,
                                   HelpExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class ExtensionRegistry(object):

    def __init__(self, bot, load=True):
        self.bot = bot
        self.extensions = set()
        self.extension_names = set()
        self.disabled_extensions = {}  # Per-channel blacklist

        if load:
            self.load()

        # Core things
        self.control = ControlExtension(self, bot)
        self.help = HelpExtension(self, bot)

    def _make_import_args(self, path):
        return path, {}, {}, [path.split('.')[-1]]

    def _get_possible_extensions(self, mod):
        return filter(lambda x: not x.startswith('__'), dir(mod))

    def load_module_members(self, module):
        # See if there are any HelgaExtensions
        for member in self._get_possible_extensions(module):
            cls = getattr(module, member)
            if cls == HelgaExtension:
                continue

            try:
                if issubclass(cls, HelgaExtension) and cls.__name__ not in self.extension_names:
                    self.extensions.add(cls(bot=self.bot))
                    self.extension_names.add(cls.__name__)
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

    def _iter_call(self, fn_attr, nick, channel, message, is_public, ignore=None, invert=False):
        """
        Iterates a call over all loaded extensions
        """
        for ext in self.extensions:
            try:
                if (invert and isinstance(ext, ignore)) or (not invert and not isinstance(ext, ignore)):
                    continue
            except TypeError:
                pass

            if self.is_disabled_extension(ext, channel):
                logger.info('Skipping disabled extension %s on %s' % (ext.__class__.__name__, channel))

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

    def dispatch_extensions(self, dispatch_type, nick, channel, message, is_public):
        # This is kind of crappy, but commands should go first
        args = [dispatch_type, nick, channel, message, is_public]
        resp, message = self._iter_call(*args, ignore=CommandExtension)

        if resp:
            return resp, message
        else:
            # We have to update the message. It might have changed
            args[3] = message

        return self._iter_call(*args, ignore=CommandExtension, invert=True)

    def dispatch_core(self, dispatch_type, nick, channel, message, is_public):
        """
        Calls a given method name of the core extensions
        """
        # Handle the CTL interface
        resp = getattr(self.control, dispatch_type)(nick, channel, message, is_public)

        # Fix this garbage
        if dispatch_type == 'pre_dispatch':
            resp, message = resp

        if resp:
            return resp, message

        # Handle the HELP interface
        return getattr(self.help, dispatch_type)(nick, channel, message, is_public)

    def on(self, event, *args, **kwargs):
        """
        Generalize event delegator. Sends event to all loaded extensions
        """
        self.control.on(event, *args, **kwargs)
        self.help.on(event, *args, **kwargs)

        for ext in self.extensions:
            ext.on(event, *args, **kwargs)

    def dispatch_type(self, dispatch_type, nick, channel, message, is_public):
        """
        Sends a "dispatch" like action to each extension
        """
        return self.dispatch_extensions(dispatch_type, nick, channel, message, is_public)

    def pre_dispatch(self, nick, channel, message, is_public):
        return self.dispatch_type('pre_dispatch', nick, channel, message, is_public)

    def dispatch(self, nick, channel, message, is_public):
        return self.dispatch_type('dispatch', nick, channel, message, is_public)

    def is_disabled_extension(self, name_or_cls, channel):
        """
        Returns True or False if extension is disabled on the given channel
        """
        if isinstance(name_or_cls, type):
            name = name_or_cls.__class__.__name__
        else:
            name = name_or_cls

        return name in self.disabled_extensions.get(channel, set())

    def disable_extension(self, name, channel):
        """
        Disables the use of a named extension on a given channel
        """
        if channel not in self.disabled_extensions:
            self.disabled_extensions[channel] = set()

        if name not in self.extension_names:
            return False

        logger.info('Disabling %s on %s' % (name, channel))
        self.disabled_extensions[channel].add(name)

    def enabled_extensions(self, channel):
        """
        Returns a set of extensions enabled on this channel
        """
        return self.extension_names - self.disabled_extensions.get(channel, set())
