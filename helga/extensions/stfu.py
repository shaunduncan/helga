import random

from helga.extensions.base import CommandExtension


class STFUExtension(CommandExtension):
    """
    Toggles helga's level of vocal-ness on any given channel
    """
    NAME = 'stfu'

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

    def preprocess(self, message):
        # A hack, we hook into how commands work
        super(STFUExtension, self).process(message)

        if self.is_silenced(message.on_channel):
            message.message = ''

    def handle_message(self, opts, message):
        if message.is_public:
            if opts['stfu']:
                message.response = self.silence(message.on_channel)

            elif opts['speak']:
                message.response = self.unsilence(message.on_channel)
        else:
            # Be an asshole
            message.response = random.choice(self.snarks)

    def is_silenced(self, channel):
        return channel in self.silenced

    def silence(self, channel):
        was_silenced = channel in self.silenced
        self.silenced.add(channel)
        if not was_silenced:
            return random.choice(self.silence_acks)

    def unsilence(self, channel):
        was_silenced = channel in self.silenced
        self.silenced.discard(channel)
        if was_silenced:
            return random.choice(self.unsilence_acks)
