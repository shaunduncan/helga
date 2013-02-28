import random
import re

from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger
from helga.util.twitter import tweet


logger = setup_logger(__name__)


class HaikuExtension(CommandExtension):

    usage = '[BOTNICK] haiku [tweet|about (<thing> ...)|(add|add_use|use|remove) (fives|sevens) (INPUT ...)]'

    syllable_map = {
        'fives': 5,
        'sevens': 7,
    }

    last = {}

    def firstof(self, dictionary, *keys):
        """
        Returns key of first non-falsey value in dictionary by checking keys that match
        a list of argument strings
        """
        for k, v in dictionary.iteritems():
            if k in keys and v:
                return k

    def handle_message(self, opts, nick, channel, message, is_public):
        response = None

        if opts['tweet']:
            response = self.tweet(channel)
        elif opts['about']:
            response = self.make_poem(about=' '.join(opts['<thing>']))
        else:
            fn_name = self.firstof(opts, 'add', 'add_use', 'use', 'remove')
            if fn_name:
                input = ' '.join(opts['INPUT'] or [])
                syllables = self.syllable_map.get(self.firstof(opts, 'fives', 'sevens'), None)
                call_me_maybe = getattr(self, fn_name, None)

                if call_me_maybe:
                    response = call_me_maybe(syllables, input)

            # just make a poem
            else:
                response = self.make_poem()

        # It's a poem, dude
        if isinstance(response, list):
            self.last[channel] = response

        return response

    def _make_term_pattern(self, term):
        return re.compile(term, re.I)

    def get_random_line(self, syllables, about=None):
        """
        Returns a single random line with the given number of syllables.
        Optionally will find lines containing a keyword. If no entries are found
        with that keyword, we just return a random one
        """
        finder = {
            'syllables': syllables
        }

        if about:
            finder.update({
                'message': {'$regex': self._make_term_pattern(about)}
            })

        qs = db.haiku.find(finder)
        num_rows = qs.count()

        if num_rows == 0:
            return None if not about else self.get_random_line(syllables)

        skip = random.randint(0, num_rows - 1)

        # Bleh, this is how we randomly grab one
        return str(qs.limit(-1).skip(skip).next()['message'])

    def tweet(self, channel):
        if channel not in self.last:
            return "%(nick)s, why don't you try making one first?"

        # fives / sevens / fives
        resp = tweet(' / '.join(self.last[channel]))

        # This will keep it from over tweeting
        del self.last[channel]

        if not resp:
            resp = '%(nick)s that probably did not work'

        return resp

    def add(self, syllables, message):
        logger.info('Adding %d syllable line: %s' % (syllables, message))

        db.haiku.insert({
            'syllables': syllables,
            'message': message,
        })

        return random.choice(self.add_acks)

    def add_use(self, syllables, message):
        """
        Stores a poem message and uses it in the response
        """
        self.add(syllables, message)
        return self.use(syllables, message)

    def use(self, syllables, message):
        """
        Uses a message in a poem without storing it
        """
        poem = self.make_poem()

        if syllables == 5 and message not in poem:
            which = random.choice([0, 2])
            poem[which] = message
        elif syllables == 7:
            poem[1] = message

        return poem

    def remove(self, syllables, message):
        logger.info('Removing %s syllable line: %s' % (syllables, message))

        db.haiku.remove({
            'syllables': syllables,
            'message': message
        })

        return random.choice(self.delete_acks)

    def make_poem(self, about=None):
        poem = [
            self.get_random_line(5, about),
            self.get_random_line(7, about),
            self.get_random_line(5, about)
        ]

        if not all(poem):
            return None

        return poem
