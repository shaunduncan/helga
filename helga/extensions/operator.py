import random

import smokesignal

from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class OperatorExtension(CommandExtension):

    NAME = 'oper'

    usage = '[BOTNICK] oper ((join|leave|autojoin (add|remove)) <channel>)'
    nopes = [
        "You're not the boss of me",
        "Whatever I do what want",
        "You can't tell me what to do",
        "%(nick)s, this incident has been reported",
        "NO. You are now on notice %(nick)s"
    ]

    def __init__(self, *args, **kwargs):
        # Hack for le instance callbacks
        @smokesignal.on('signon')
        def callback():
            if db is not None:
                self.join_autojoined_channels()

        super(OperatorExtension, self).__init__(*args, **kwargs)

    def is_operator(self, nick):
        return nick in self.bot.operators

    def handle_message(self, opts, message):
        if not self.is_operator(message.from_nick):
            message.response = random.choice(self.nopes)
            return

        if opts['autojoin']:
            channel = opts['<channel>']

            if not channel.startswith('#'):
                channel = '#' + channel

            if opts['add']:
                message.response = self.add_autojoin(channel)
            elif opts['remove']:
                message.response = self.remove_autojoin(channel)
        elif opts['join']:
            self.join(opts['<channel>'])
        elif opts['leave']:
            self.leave(opts['<channel>'])

    def join_autojoined_channels(self):
        for channel in db.autojoin.find():
            try:
                # Damn mongo unicode messin with my twisted
                self.bot.client.join(str(channel['channel']))
            except:
                logger.exception('Could not autojoin %s' % channel['channel'])

    def join(self, channel):
        self.bot.client.join(str(channel))

    def leave(self, channel):
        self.bot.client.leave(str(channel))

    def add_autojoin(self, channel):
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

    def remove_autojoin(self, channel):
        """
        Removes a channel as an autojoin
        """
        logger.info('Removing Autojoin %s' % channel)
        db.autojoin.remove({'channel': channel})
        return self.random_ack()
