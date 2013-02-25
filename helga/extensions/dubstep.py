import random
import re
import time

from helga.extensions.base import HelgaExtension


class DubstepExtension(HelgaExtension):

    _since = None
    _since_count = 0

    def dispatch(self, nick, channel, message, is_public):
        if not re.match(r'dubstep', message):
            return

        if self._since and (time.time() - self._since) < 10 and self._since_count >= 3:
            self._since = None
            self._since_count = 0
            return 'STOP! MY HEAD IS VIBRATING!'

        if not self._since:
            self._since = time.time()

        self._since_count += 1
        return 'wub' * random.randint(5, 25)
