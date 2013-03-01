from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class ControlExtension(CommandExtension):
    """
    Helga's control surface. Anyone can tell her what to do
    """
    usage = '[BOTNICK] ctl (extension (list|disable <ext>))'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)

    def handle_message(self, opts, nick, channel, message, is_public):
        if opts['extension']:
            return self.extension_ctl(opts, channel)

    def extension_ctl(self, opts, channel):
        if opts['list']:
            return self.list_channel_extensions(channel)
        elif opts['disable']:
            return self.disable_channel_extension(opts['<ext>'], channel)

    def list_channel_extensions(self, channel):
        enabled = self.registry.enabled_extensions(channel)

        logger.info('Currently enabled: %s' % enabled)

        # This is converted to multiple lines
        return ['Extensions on this channel:'] + list(enabled)

    def disable_channel_extension(self, ext_name, channel):
        if self.registry.disable_extension(ext_name, channel):
            return self.random_ack()
        else:
            return "Sorry %(nick)s, don't know that one. Try `" + self.bot.nick + " ctl extension list`"


class HelpExtension(CommandExtension):
    """
    Helga can help you out. You can look for the usage of any loaded extension
    """
    usage = '[BOTNICK] help <name>'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)
