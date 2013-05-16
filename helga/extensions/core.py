import smokesignal

from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class ControlExtension(CommandExtension):
    """
    Helga's control surface. Anyone can tell her what to do
    """
    NAME = 'controls'
    usage = '[BOTNICK] extension (list <type>|(disable|enable) <ext>)'

    def __init__(self, registry, *args, **kwargs):
        self.registry = registry

        # Hack for le instance callbacks
        @smokesignal.on('signon')
        def callback():
            if db is not None:
                self._init_disabled()

        super(CommandExtension, self).__init__(*args, **kwargs)

    def handle_message(self, opts, message):
        if opts['extension']:
            if opts.get('list', False):
                message.response = self.list_extensions(message.channel, type=opts.get('<type>', 'all'))
            elif opts.get('disable', False):
                message.response = self.disable_extension(opts['<ext>'], message.channel)
            elif opts.get('enable', False):
                message.response = self.enable_extension(opts['<ext>'], message.channel)

    def _list_enabled_extensions(self, channel):
        enabled = self.registry.get_enabled(channel)
        return 'Enabled extensions on %s: %s' % (channel, ', '.join(enabled))

    def _list_disabled_extensions(self, channel):
        disabled = self.registry.get_disabled(channel)
        print type(disabled)
        return 'Disabled extensions on %s: %s' % (channel, ', '.join(disabled))

    def list_extensions(self, channel, type='all'):
        # Ensure a usable default
        if not type:
            type = 'all'

        type = type.lower()

        if type == 'enabled':
            return self._list_enabled_extensions(channel)
        elif type == 'disabled':
            return self._list_disabled_extensions(channel)
        else:
            # Multiple lines
            return [
                self._list_enabled_extensions(channel),
                self._list_disabled_extensions(channel),
            ]

    def _init_disabled(self):
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
                    db.disabled_extensions.save(rec)

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
                    db.disabled_extensions.save(rec)

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
        resp = []

        for ext in self.registry.get_all_extensions(core=True):
            if not hasattr(ext, 'NAME') or not hasattr(ext, 'usage'):
                continue
            resp.append(fmt % (ext.NAME, self.no_botnick(ext.usage)))

        if resp:
            return resp

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

            # Side effect - this extension PMs the user asking
            message.resp_channel = message.from_nick


class IgnoreExtension(CommandExtension):
    """
    Tell helga to ignore certain people/bots
    """

    NAME = 'ignore'
    usage = '[BOTNICK] ignore (list|(add|remove) <nick>)'

    def preprocess(self, message):
        # Here so the user can't you know...unignore themselves
        if self.is_ignoring(message.from_nick, message.channel):
            logger.info('Ignoring message from %s on %s' % (message.from_nick, message.channel))
            message.message = ''

        # A hack, we hook into how commands work
        super(IgnoreExtension, self).process(message)

    def is_ignoring(self, nick, channel):
        return db.ignores.find_one({
            'channel': channel,
            'nicks': {'$in': [nick]}
        }) is not None

    def handle_message(self, opts, message):
        response = None

        if opts['list']:
            response = self.list_ignore(message.channel)
        elif opts['add']:
            if message.from_nick == opts['<nick>']:
                response = 'Why on earth would you want to do that?'
            elif opts['<nick>'] in self.bot.operators:
                response = 'I will never not listen to %s' % opts['<nick>']
            else:
                response = self.add_ignore(opts['<nick>'], message.channel)
        elif opts['remove']:
            response = self.remove_ignore(opts['<nick>'], message.channel)

        if response:
            message.response = response

    def list_ignore(self, channel):
        result = db.ignores.find_one({'channel': channel})

        if result and result['nicks']:
            return 'Ignoring these nicks on this channel: ' + ', '.join(result['nicks'])
        else:
            return "I'm not ignoring anyone on this channel"

    def _init_db_rec(self, channel, nick=None):
        nicks = [nick] if nick else []
        if db.ignores.find({'channel': channel}).count() == 0:
            logger.info('Initialize ignores %s on %s' % (nick, channel))
            db.ignores.insert({'channel': channel, 'nicks': nicks})

    def add_ignore(self, nick, channel, nodb=False):
        if nodb:
            return

        self._init_db_rec(channel, nick)

        rec = db.ignores.find_one({'channel': channel})
        if nick not in rec['nicks']:
            logger.info('Adding ignore %s on %s' % (nick, channel))
            rec['nicks'].append(nick)
            db.ignores.save(rec)

        return self.random_ack()

    def remove_ignore(self, nick, channel, nodb=False):
        if nodb:
            return

        self._init_db_rec(channel, nick)

        rec = db.ignores.find_one({'channel': channel})
        if nick in rec['nicks']:
            logger.info('Removing ignore %s on %s' % (nick, channel))
            rec['nicks'].remove(nick)
            db.ignores.save(rec)

        return self.random_ack()
