import re

from collections import defaultdict

from helga.extensions.base import ContextualExtension


class MTSExtension(ContextualExtension):
    """
    Allows channel members to do things like s/foo/bar/ on their last message
    """
    NAME = 'meanttosay'

    context = r'(^|.*\s)s/(\w+)/(\w*?)/?($|\s.*)'
    allow_many = False
    response_fmt = '%(nick)s meant to say: %(response)s'

    def __init__(self, *args, **kwargs):
        super(MTSExtension, self).__init__(*args, **kwargs)
        self.last = defaultdict(dict)

    def process(self, message):
        # Contextualize first. If no response, record the message
        super(MTSExtension, self).process(message)

        if not message.has_response:
            self.record_last(message)
        else:
            self.clear_last(message)

    def clear_last(self, message):
        self.last[message.channel][message.from_nick] = ''

    def record_last(self, message):
        self.last[message.channel][message.from_nick] = message.message

    def get_last(self, message):
        if message.from_nick not in self.last[message.channel]:
            self.clear_last(message)

        return self.last[message.channel][message.from_nick]

    def contextualize(self, message):
        # Specific behavior to we can get the previous message
        last = self.get_last(message)
        match = re.match(self.context, message.message, re.I)

        if match is None or (match and not last):
            return

        find, replace = match.groups()[1:3]
        meant_to_say = re.sub(find, replace, last)

        # Copypasta from parent class
        message.response = self.response_fmt % {
            'nick': '%(nick)s',  # Yes, this is annoying, but whatever
            'response': meant_to_say
        }
