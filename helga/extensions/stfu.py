import re
import random

from helga.extensions.base import CommandExtension


class STFUExtension(CommandExtension):
    """
    Toggles helga's level of vocal-ness on any given channel
    """

    usage = '[BOTNICK] (stfu|speak)'

    silence_acks = (
        'silence is golden',
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

    def __init__(self, *args, **kwargs):
        self.silenced = set()
        super(STFUExtension, self).__init__(*args, **kwargs)

    def dispatch(self, nick, channel, message, is_public):
        pass

    def pre_dispatch(self, nick, channel, message, is_public):
        resp = super(STFUExtension, self).dispatch(nick, channel, message, is_public)

        if not isinstance(resp, tuple):
            return resp, message if not self.is_silenced(channel) else ''

        return resp

    def handle_message(self, opts, nick, channel, message, is_public):
        was_silenced = self.is_silenced(channel)

        if is_public:
            if opts['stfu']:
                self.silence(channel)
                return random.choice(self.silence_acks) if not was_silenced else None, ''

            elif opts['speak']:
                self.unsilence(channel)
                return random.choice(self.unsilence_acks) if was_silenced else None, ''
        else:
            # Be an asshole
            return random.choice(self.snarks), ''

        if self.is_silenced(channel):
            return None, ''

    def is_silenced(self, channel):
        return channel in self.silenced

    def silence(self, channel):
        self.silenced.add(channel)

    def unsilence(self, channel):
        self.silenced.discard(channel)
