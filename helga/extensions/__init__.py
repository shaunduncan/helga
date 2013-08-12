import pkg_resources
from helga import settings
from helga.extensions.base import (HelgaExtension,
                                   CommandExtension)
from helga.extensions.core import (ControlExtension,
                                   HelpExtension,
                                   IgnoreExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class ExtensionRegistry(object):

    def __init__(self, bot, load=True):
        self.bot = bot
        self.extensions = {'commands': set(), 'contexts': set()}
        self.extension_names = set()
        self.disabled_extensions = {}  # Per-channel blacklist
        self.core = set()

        if load:
            self.load()

    def _make_import_args(self, path):
        return path, {}, {}, [path.split('.')[-1]]

    def load_module_members(self, cls):
        try:
            if issubclass(cls, HelgaExtension) and cls.NAME not in self.extension_names:
                category = 'commands' if self._is_command(cls) else 'contexts'
                self.extensions[category].add(cls(bot=self.bot))
                self.extension_names.add(cls.NAME)
        except (TypeError, AttributeError):
            # Either it's not a class, or it doesn't have ``NAME``
            logger.error('Attempted to load a non-plugin: %s' % repr(cls))

    def load(self):
        for module in _load_library_extensions():
            logger.debug('Loading extension extension %s' % repr(module))
            self.load_module_members(module)

        # XXX Core has already loaded :/
        # Core loading
        self.core = set([
            ControlExtension(self, self.bot),
            HelpExtension(self, self.bot),
            IgnoreExtension(self.bot),
        ])

    def _is_command(self, ext):
        """
        Checks if an extension is a command or not
        """
        try:
            return issubclass(ext, CommandExtension)
        except TypeError:
            return False

    def _call_extension_method(self, fn, message):
        """
        Calls a function name for all extensions
        """
        # TODO: process core first

        # Nested for your pleasure
        def call_fn(fn, message, category):
            for ext in self.extensions[category]:
                if self.is_disabled(ext, message.channel):
                    logger.debug('Skipping disabled extension %s on %s' % (ext.NAME, message.channel))
                    continue

                getattr(ext, fn)(message)

                if message.has_response:
                    return

        # Do cores first
        for ext in self.core:
            getattr(ext, fn)(message)
            if message.has_response:
                return

        # This is kind of crappy, but commands should go first
        call_fn(fn, message, 'commands')

        # The other ones
        if not message.has_response:
            call_fn(fn, message, 'contexts')

    def preprocess(self, message):
        """
        Used to do any message preprocessing. i.e. transforming things
        """
        self._call_extension_method('preprocess', message)

    def process(self, message):
        self._call_extension_method('process', message)

    def is_disabled(self, name, channel):
        """
        Returns True or False if extension is disabled on the given channel
        """
        # If it's an extension class/object
        if hasattr(name, 'NAME'):
            name = name.NAME

        return name in self.disabled_extensions.get(channel, set())

    def is_enabled(self, name, channel):
        return not self.is_disabled(name, channel)

    def disable(self, name, channel):
        """
        Disables the use of a named extension on a given channel
        """
        if channel not in self.disabled_extensions:
            self.disabled_extensions[channel] = set()

        if name not in self.extension_names:
            return False

        logger.info('Disabling %s on %s' % (name, channel))
        self.disabled_extensions[channel].add(name)

        return True

    def enable(self, name, channel):
        """
        Enables the use of a named extension on a given channel
        """
        if channel not in self.disabled_extensions:
            self.disabled_extensions[channel] = set()

        if name not in self.extension_names:
            return False

        logger.info('Enabling %s on %s' % (name, channel))
        self.disabled_extensions[channel].discard(name)

        return True

    def get_enabled(self, channel):
        """
        Returns a set of extensions enabled on this channel
        """
        return self.extension_names - self.get_disabled(channel)

    def get_disabled(self, channel):
        """
        Returns a set of extensions disabled on this channel
        """
        return self.disabled_extensions.get(channel, set())

    def get_all_extensions(self, core=False):
        extensions = self.extensions['commands'].union(self.extensions['contexts'])

        if core:
            extensions = extensions.union(self.core)

        return extensions

    def get_commands(self):
        return self.extensions['commands']

    def get_contexts(self):
        return self.extensions['contexts']

    def is_extension_name(self, name):
        return name in self.extension_names


#
# Plugin loader Helpers
#

def _load_library_extensions():
    """
    Locate all setuptools entry points by the name 'helga_handlers'
    and initialize them.
    Any third-party library may register an entry point by adding the
    following to their setup.py::

        entry_points = {
            'helga_handlers': [
                'plugin_name = mylib.mymodule:Handler_Class',
            ],
        },

    """
    group = 'helga_handlers'
    entry_points = pkg_resources.iter_entry_points(group=group)
    plugins = []
    for ep in entry_points:
        try:
            logger.debug('loading %s' % ep.name)
            plugin = ep.load()
            plugin._helga_name_ = ep.name
            plugins.append(plugin)
        except Exception as error:
            logger.error("Error initializing plugin %s: %s" % (ep, error))
    return plugins
