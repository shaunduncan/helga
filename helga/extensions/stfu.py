import re
import random

from helga.extensions.base import HelgaExtension


__all__ = ['stfu']


class STFU(HelgaExtension):
    """
    Toggles helga's level of vocal-ness on any given channel
    """

    silence_acks = (
        'slience is golden',
        'shutting up',
        'biting my tongue',
        'fine, whatever',
    )

    unsilence_acks = (
        'speaking once again',
        'did you miss me?',
        'FINALLY',
        'thanks %(nick)s, i was getting bored'
    )

    snarks = (
        'why would you want to do that %(nick)s?',
        'do you really despise me that much %(nick)s?',
        'whatever i do what i want',
        'no can do, i love the sound of my own voice',
    )

    def __init__(self):
        # A list of where helga is silent
        self._silenced = set()

    def handle_public(self, bot, channel, message):
        if message == '%s stfu' % bot.nick:
            self._silenced.add(channel)
            return random.choice(self.silence_acks)
        elif message == '%s speak' % bot.nick:
            self._silenced.discard(channel)
            return random.choice(self.unsilence_acks)

    def handle_private(self, bot, message):
        if re.match(r'^(%s )?(stfu|speak)$' % bot.nick, message):
            return random.choice(self.snarks)

    def dispatch(self, bot, nick, channel, message, is_public):
        message = message.lower()

        if not is_public:
            response = self.handle_private(bot, message)
        else:
            response = self.handle_public(bot, channel, message)

        return response

    def is_silenced(self, channel):
        return channel in self._silenced


stfu = STFU()
