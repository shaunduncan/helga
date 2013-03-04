from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class ControlExtension(CommandExtension):
    """
    Helga's control surface. Anyone can tell her what to do
    """
    NAME = 'controls'
    usage = '[BOTNICK] extension (list|(disable|enable) <ext>)'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)

    def handle_message(self, opts, message):
        if opts['extension']:
            if opts.get('list', False):
                message.response = self.list_extensions(message.channel)
            elif opts.get('disable', False):
                message.response = self.disable_extension(opts['<ext>'], message.channel)
            elif opts.get('enable', False):
                message.response = self.enable_extension(opts['<ext>'], message.channel)

    def list_extensions(self, channel):
        enabled = self.registry.get_enabled(channel)

        # This is converted to multiple lines
        return 'Extensions on this channel: ' + ', '.join(enabled)

    def on(self, event, *args, **kwargs):
        if event == 'signon':
            for rec in db.disabled_extensions.find():
                for channel in rec['channels']:
                    self.disable_extension(rec['extension'], channel, nodb=True)

    def _init_db_rec(self, ext, channel=None):
        channels = [channel] if channel else []
        if db.disabled_extensions.find({'extension': ext}).count() == 0:
            logger.info('Initializing autodisable %s on %s' % (ext, channel))
            db.disabled_extensions.insert({'extension': ext, 'channels': channels})

    def disable_extension(self, ext_name, channel, nodb=False):
        if self.registry.disable(ext_name, channel):
            if not nodb:
                self._init_db_rec(ext_name, channel)

                rec = db.disabled_extensions.find_one({'extension': ext_name})
                if channel not in rec['channels']:
                    logger.info('Adding autodisable %s on %s' % (ext_name, channel))
                    rec['channels'].append(channel)
                    rec.save()

            return self.random_ack()
        else:
            return "Sorry %(nick)s, don't know that one. Try `" + self.bot.nick + " extension list`"

    def enable_extension(self, ext_name, channel, nodb=False):
        if self.registry.enable(ext_name, channel):
            if not nodb:
                self._init_db_rec(ext_name, channel)

                rec = db.disabled_extensions.find_one({'extension': ext_name})
                if channel in rec['channels']:
                    logger.info('Removing autodisable %s on %s' % (ext_name, channel))
                    rec['channels'].remove(channel)
                    rec.save()

            return self.random_ack()
        else:
            return "Sorry %(nick)s, don't know that one. Try `" + self.bot.nick + " extension list`"


class HelpExtension(CommandExtension):
    """
    Helga can help you out. You can look for the usage of any loaded extension
    """
    NAME = 'help'
    usage = '[BOTNICK] (help|halp) [<name>]'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry
        super(CommandExtension, self).__init__(*args, **kwargs)

    def no_botnick(self, ext):
        return ext.replace('[BOTNICK]', self.bot.nick).strip()

    def help_all(self):
        fmt = '%s: %s'
        return [fmt % (e.NAME, self.no_botnick(e.usage)) for e in self.registry.get_commands()]

    def help(self, name):
        for ext in self.registry.get_all_extensions(core=True):
            if getattr(ext, 'NAME', '') != name or not hasattr(ext, 'usage'):
                continue

            return 'USAGE: %s' % self.no_botnick(ext.usage)

        return "Sorry %(nick)s, don't know that one"

    def handle_message(self, opts, message):
        if opts['help'] or opts['halp']:
            ext_name = opts.get('<name>', '')
            message.response = self.help(ext_name) if ext_name else self.help_all()
