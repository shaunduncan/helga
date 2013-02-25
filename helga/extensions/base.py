import random


class HelgaExtension(object):
    """
    Defines a dispatchable API for extensions and extra functionality
    """
    acks = (
        'roger',
        '10-4',
        'no problem %(nick)s',
        'will do',
        'you got it %(nick)s',
        'anything you say %(nick)s',
        'sure thing',
        'ok',
        'right-o',
    )

    add_acks = acks + (
        '%(nick)s, added',
        'consider it done',
    )

    delete_acks = acks + (
        '%(nick)s, deleted',
        'nuking from orbit',
        'consider it done',
        "annnnd it's gone",
    )

    def __init__(self, bot):
        self.bot = bot

    def pre_dispatch(self, nick, channel, message, is_public):
        """
        Any filter-type action that should happen before dispatch is called
        """
        return None

    def dispatch(self, nick, channel, message, is_public):
        return None

    def random_ack(self):
        return random.choice(self.acks)
