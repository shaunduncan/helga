from helga import settings
from helga.extensions.base import ContextualExtension


class ReviewboardExtension(ContextualExtension):

    NAME = 'reviewboard'

    context = r'cr([\d]+)'
    allow_many = True
    response_fmt = '%(nick)s might be talking about codereview: %(response)s'

    def transform_match(self, match):
        return settings.REVIEWBOARD_URL % {'review': match}
