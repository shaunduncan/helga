import random

from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class OperatorExtension(CommandExtension):

    usage = '[BOTNICK] oper (join|leave) <channel>'
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
            return self.join_channel(channel)
        elif opts['leave']:
            return self.leave_channel(channel)

    def join_channel(self, channel):
        logger.info('Joining %s' % channel)
        self.bot.client.join(channel)
        return self.random_ack()

    def leave_channel(self, channel):
        logger.info('Leaving %s' % channel)
        self.bot.client.leave(channel)
        return self.random_ack()
