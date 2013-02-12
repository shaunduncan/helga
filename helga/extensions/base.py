import random


class HelgaExtension(object):
    """
    Defines a dispatchable API for extensions and extra functionality
    """
    acks = (
        'roger',
        '10-4',
        'no problem',
        'will do',
        'you got it boss',
        'anything you say',
        'sure thing',
        'ok',
        'right-o',
    )

    def dispatch(self, bot, nick, channel, message, is_public):
        raise NotImplementedError

    def random_ack(self):
        return random.choice(self.acks)
