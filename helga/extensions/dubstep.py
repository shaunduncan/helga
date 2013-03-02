import random
import time

from helga.extensions.base import ContextualExtension


class DubstepExtension(ContextualExtension):
    """
    Dubstep can be described as a rapid succession of wub wubs, wow wows, and yep yep yep yeps
    """
    NAME = 'dubstep'

    context = r'dubstep'
    allow_many = False
    response_fmt = '%(response)s'

    wub_count = 0
    max_wubs = 3
    last_wub = None
    wub_timeout = 10

    def transform_match(self, match):
        if self.last_wub and (time.time() - self.last_wub) > self.wub_timeout:
            self.wub_count = 0

        if self.wub_count >= self.max_wubs:
            self.wub_count = 0
            self.last_wub = time.time()

            return 'STOP! MY HEAD IS VIBRATING'
        else:
            self.wub_count += 1
            self.last_wub = time.time()

            return 'wubwub' * self.wub_count * random.randint(1, 4)
