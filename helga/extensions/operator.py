import re

from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class OperatorExtension(HelgaExtension):

    nope = "You're not the boss of me"
    command_pat = r'^(%s )?oper (join|leave) (.*)$'

    def is_operator(self, nick):
        return nick in self.bot.operators

    def parse_command(self, message):
        parts = re.findall(self.command_pat % self.bot.nick, message, re.I)

        if not parts:
            return None, None, None

        return parts[0]

    def dispatch(self, nick, channel, message, is_public):
        botnick, cmd, details = self.parse_command(message)

        if not cmd or (is_public and not botnick):
            return None

        if not self.is_operator(nick):
            return self.nope

        if cmd in ('join', 'leave'):
            channel = details.strip()
            if not channel.startswith('#'):
                channel = '#%s' % channel
            
            try:
                getattr(self.bot.client, cmd)(channel)
            except Exception, e:
                return 'I tried, but this happened: %s' % e

            return self.random_ack()
