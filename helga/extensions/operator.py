import random

from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class OperatorExtension(CommandExtension):

    usage = '[BOTNICK] oper (join|leave|autojoin|no_autojoin) <channel>'
    nopes = [
        "You're not the boss of me",
        "Whatever I do what want",
        "You can't tell me what to do",
        "%(nick)s, this incident has been reported",
        "NO. You are now on notice %(nick)s"
    ]

    def is_operator(self, nick):
        return nick in self.bot.operators

    def handle_message(self, opts, nick, channel, message, is_public):
        if not self.is_operator(nick):
            return random.choice(self.nopes)

        channel = opts['<channel>']

        if not channel.startswith('#'):
            channel = '#' + channel

        if opts['join']:
            return self.join(channel)
        elif opts['leave']:
            return self.leave(channel)
        elif opts['autojoin']:
            return self.autojoin(channel)
        elif opts['no_autojoin']:
            return self.no_autojoin(channel)

    def on(self, event, *args, **kwargs):
        if event == 'signon':
            self.join_autojoined_channels()

    def join_autojoined_channels(self):
        for channel in db.autojoin.find():
            # Damn mongo unicode messin with my twisted
            self.bot.client.join(str(channel['channel']))

    def autojoin(self, channel):
        """
        Stores a channel as an autojoin for later
        """
        logger.info('Autojoin %s' % channel)
        db_opts = {'channel': channel}

        if db.autojoin.find(db_opts).count() == 0:
            db.autojoin.insert(db_opts)
            return self.random_ack()
        else:
            return "I'm already doing that"

    def no_autojoin(self, channel):
        """
        Removes a channel as an autojoin
        """
        logger.info('Removing Autojoin %s' % channel)
        db.autojoin.remove({'channel': channel})
        return self.random_ack()

    def join(self, channel):
        logger.info('Joining %s' % channel)
        self.bot.client.join(channel)
        return self.random_ack()

    def leave(self, channel):
        logger.info('Leaving %s' % channel)
        self.bot.client.leave(channel)
        return self.random_ack()
