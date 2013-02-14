import re
import random

from helga.bot import helga
from helga.extensions.base import HelgaExtension


class STFUExtension(HelgaExtension):
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

    STFU = 'stfu'
    SPEAK = 'speak'

    def __init__(self):
        # A list of where helga is silent
        self._silenced = set()

    def get_command(self, message, nick_required=True):
        matches = re.findall('^(%s )?([a-z0-9]+)$' % helga.nick, message)

        if matches:
            nick, command = matches[0]

            if not nick and nick_required:
                return None

            return command

    def dispatch(self, nick, channel, message, is_public):
        command = self.get_command(message.lower(), nick_required=not is_public)

        if is_public:
            was_silenced = self.is_silenced(channel)

            if command == self.STFU:
                self.silence(channel)
                return random.choice(self.silence_acks) if not was_silenced else None
            elif command == self.SPEAK:
                self.unsilence(channel)
                return random.choice(self.unsilence_acks) if was_silenced else None
        elif command in (self.STFU, self.SPEAK):
            # Be an asshole
            return random.choice(self.snarks)

    def is_silenced(self, channel):
        return channel in self._silenced

    def silence(self, channel):
        self._silenced.add(channel)

    def unsilence(self, channel):
        self._silenced.discard(channel)
