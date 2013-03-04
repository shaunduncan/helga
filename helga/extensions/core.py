from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class ControlExtension(CommandExtension):
    """
    Helga's control surface. Anyone can tell her what to do
    """
    usage = '[BOTNICK] extension (list|disable <ext>)'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)

    def handle_message(self, opts, message):
        if opts['extension'] and opts.get('list', False):
            message.response = self.list_extensions(opts, message.channel)
        elif opts['extension'] and opts.get('disable', False):
            message.response = self.disable_extension(opts['<ext>'], message.channel)

    def list_extensions(self, channel):
        enabled = self.registry.enabled_extensions(channel)

        logger.info('Currently enabled: %s' % enabled)

        # This is converted to multiple lines
        return 'Extensions on this channel: ' + ', '.join(enabled)

    def disable_extension(self, ext_name, channel):
        if self.registry.disable_extension(ext_name, channel):
            return self.random_ack()
        else:
            return "Sorry %(nick)s, don't know that one. Try `" + self.bot.nick + " extension list`"


class HelpExtension(CommandExtension):
    """
    Helga can help you out. You can look for the usage of any loaded extension
    """
    usage = '[BOTNICK] (help|halp) [<name>]'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)

    def no_botnick(self, ext):
        return ext.replace('[BOTNICK]', self.bot.nick).strip()

    def help_all(self):
        fmt = '%s usage: %s'
        return [fmt % (e.NAME, self.no_botnick(e.usage)) for e in self.registry.get_commands()]

    def help(self, name):
        if self.registry.is_extension_name(name):
            for ext in self.registry.get_all_extensions():
                if getattr(ext, 'NAME', '') != name or not hasattr(ext, 'usage'):
                    continue

                return 'USAGE: %s' % ext.usage

        return "Sorry %(nick)s, don't know that one"

    def handle_message(self, opts, message):
        if opts['help'] or opts['halp']:
            ext_name = opts.get('<name>', '')
            message.response = self.help(ext_name) if ext_name else self.help_all()
