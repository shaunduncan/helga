import random
import re

from docopt import docopt, DocoptExit


class HelgaExtension(object):
    """
    Defines a dispatchable API for extensions and extra functionality

    Note: all extensions should provide class level attribute NAME that
    is a short keyword to identify it. If you don't, you'll break everything
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

    def random_ack(self):
        return random.choice(self.acks)

    def preprocess(self, message):
        """
        Any filter-type action that should happen before dispatch is called
        """
        pass

    def process(self, message):
        """
        Process a message object and attach any response to it
        """
        pass


class CommandExtension(HelgaExtension):
    """
    Command type extension. Implementers should supply a class attribute:

    usage: docopt supported string. this should _always_ start with [BOTNICK]
           unless the behavior of `should_handle_message` is altered
    """

    # This should ONLY be the argument string
    usage = '[BOTNICK] [COMMAND] [INPUT ...]'

    def parse_command(self, message):
        argv = message.message.strip().split()
        usage = self.usage

        # make sure usage is right - this is a docopt complainy thing. maybe i'll fix it.
        if not usage.lower().startswith('usage: irc '):
            usage = 'Usage: irc %s' % usage

        try:
            return docopt(usage, argv=argv, help=False)
        except DocoptExit:
            return None

    def should_handle_message(self, opts, message):
        if not opts:
            return False

        botnick = opts.get('BOTNICK', '')
        if botnick and botnick.endswith((',', ':',)):
            botnick = botnick[:-1]

        if botnick and botnick == self.bot.nick:
            return True
        elif not message.is_public and not botnick:
            return True

        return False

    def handle_message(self, opts, message):
        """
        Handle the message. This should set message.response to None if no response
        is required, a string for a single line response, or a list of
        strings for a multiline response.

        Side effect: if you specify [INPUT ...] in `usage`, it will be returned
        as a list of strings, not one single string. Sorry...
        """
        pass

    def process(self, message):
        opts = self.parse_command(message)

        if opts and self.should_handle_message(opts, message):
            self.handle_message(opts, message)


class ContextualExtension(HelgaExtension):
    """
    Contextualizes messages by responding to any match in message content.
    Implementers should provide the following class attributes:

    context: regular expression string to test against incoming messages
    allow_many: boolean. True returns all transformed matches. False returns the first
    response_fmt: response format string. Should at minimum contain format '%(response)s'.
                  optionally can contain %(nick)s to refer to the user sending the message

    Implementers should also provide a mechanism to transform a match into a readable
    string by overriding `transform_match`.
    """
    context = None
    allow_many = False
    response_fmt = '%(nick)s might be talking about: %(response)s'

    def transform_match(self, match):
        """
        Converts a single match of re.findall() using the context against the
        incoming message
        """
        return match

    def contextualize(self, message):
        found = []

        for match in re.findall(self.context, message.message, re.I):
            found.append(self.transform_match(match))

        # filter Nones
        found = filter(lambda x: x is not None, found)

        if found:
            found = found if self.allow_many else [found[0]]

            message.response = self.response_fmt % {
                'nick': '%(nick)s',  # Yes, this is annoying, but whatever
                'response': ' '.join(found)
            }

    def process(self, message):
        if self.context:
            self.contextualize(message)
