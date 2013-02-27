import re

from helga import settings
from helga.extensions.base import HelgaExtension


class ReviewboardExtension(HelgaExtension):

    review_pattern = r'cr([\d]+)'

    def contextualize(self, message):
        cr_urls = []

        for match in re.findall(self.review_pattern, message, re.I):
            cr_urls.append(settings.REVIEWBOARD_URL % {'review': match})

        if cr_urls:
            cr_text = 'codereview' + ('s' if len(cr_urls) > 1 else '')
            return '%(nick)s might be talking about ' + cr_text + ': ' + ', '.join(cr_urls)

    def dispatch(self, nick, channel, message, is_public):
        return self.contextualize(message)
