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

    def dispatch(self, bot, nick, channel, message, is_public):
        raise NotImplementedError

    def random_ack(self):
        return random.choice(self.acks)
