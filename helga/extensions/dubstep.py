import re
import time

from helga.extensions.base import HelgaExtension


class DubstepExtension(HelgaExtension):

    since = None
    since_count = 0

    FLOOD_TIME = 10
    FLOOD_MSG_LIMIT = 3

    def dispatch(self, nick, channel, message, is_public):
        if not re.match(r'dubstep', message):
            return

        if not self.since:
            self.since = time.time()

        now_diff = time.time() - self.since

        if now_diff < self.FLOOD_TIME and self.since_count >= self.FLOOD_MSG_LIMIT:
            self.since = None
            self.since_count = 0
            return 'STOP! MY HEAD IS VIBRATING!'

        if not self.since:
            self.since = time.time()

        self.since_count += 1
        return 'wubwubwub' * self.since_count * 2
