# -*- coding: utf8 -*-
import random
import re

from helga import settings
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class FredoismExtension(HelgaExtension):

    NAME = 'fredoisms'

    responses = {
        r'alfredo(deza)?': [
            "trollfredo:::everything you are doing is wrong",
            "trollfredo:::if you aren't using zsh, %(nick)s, you are doing it wrong",
            "trollfredo:::you are wrong %(nick)s",
            "trollfredo:::i have a vim plugin that shows you how wrong you are",
            "trollfredo:::i can't believe how wrong you are",
            "trollfredo:::wrong wrong wrong",
            "trollfredo:::what is dis? WRONG",
        ],

        r'random': "trollfredo:::there is no such thing as random",
    }

    def decompose_response(self, response):
        """
        Decomposes a response into a 'send as' nick and the
        reponse itself
        """
        try:
            parts = response.split(':::')
        except AttributeError:
            # For multiline responses. NOTE: this will probably break if they should nick change
            return self.decompose_response('\n'.join(response))
        else:
            if len(parts) == 2:
                return parts[0], parts[1]
            else:
                return None, parts[0]

    def find_all_matches(self, message):
        match_pat = lambda pat: re.findall(pat, message.message, re.I)
        return [data for pat, data in self.responses.iteritems() if match_pat(pat)]

    def process(self, message):
        matches = self.find_all_matches(message)

        if not matches:
            return

        response = matches[0]

        if hasattr(response, '__iter__'):
            response = random.choice(response)

        newnick, response = self.decompose_response(response)

        if getattr(settings, 'ALLOW_NICK_CHANGE', False) and newnick is not None:
            self.bot.client.setNick(newnick)

        message.response = response
