import random
import re

from helga.db import db
from helga.extensions.base import CommandExtension
from helga.log import setup_logger
from helga.util.twitter import tweet


logger = setup_logger(__name__)


class HaikuExtension(CommandExtension):

    NAME = 'haiku'

    usage = '[BOTNICK] haiku [blame|tweet|about (<thing> ...)|(add|add_use|use|remove|claim) (fives|sevens) (INPUT ...)]'

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

    def handle_message(self, opts, message):
        response = None

        if opts['tweet']:
            response = self.tweet(message.channel)
        elif opts['blame']:
            response = self.blame(message.channel)
        elif opts['about']:
            response = self.make_poem(about=' '.join(opts['<thing>']))
        else:
            fn_name = self.firstof(opts, 'add', 'add_use', 'use', 'remove')

            if fn_name:
                input = ' '.join(opts['INPUT'] or [])
                syllables = self.syllable_map.get(self.firstof(opts, 'fives', 'sevens'), None)
                call_me_maybe = getattr(self, fn_name, None)
                kwargs = {}

                if fn_name in ('add', 'add_use', 'claim'):
                    kwargs['author'] = message.from_nick

                if call_me_maybe:
                    response = call_me_maybe(syllables, input, **kwargs)

            # just make a poem
            else:
                response = self.make_poem()

        # It's a poem, dude
        if isinstance(response, list):
            self.last[message.channel] = response

        message.response = response

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
            if not about:
                return None
            else:
                return self.get_random_line(syllables)

        skip = random.randint(0, num_rows - 1)

        # Bleh, this is how we randomly grab one
        return str(qs.limit(-1).skip(skip).next()['message'])

    def tweet(self, channel):
        if channel not in self.last:
            return "%(nick)s, why don't you try making one first?"

        # fives / sevens / fives
        resp = tweet('\n'.join(self.last[channel]))

        # This will keep it from over tweeting
        del self.last[channel]

        if not resp:
            resp = '%(nick)s that probably did not work'

        return resp

    def blame(self, channel):
        """
        Show who helped make the last haiku possible
        """
        if channel not in self.last:
            return "%(nick)s, why don't you try making one first?"

        authors = []

        for line in self.last[channel]:
            try:
                rec = db.haiku.find_one({'message': line})
            except:
                authors.append(self.bot.nick)
            else:
                authors.append(rec.get('author', None) or self.bot.nick)

        return "The last poem was brought to you by (in order): %s" % ', '.join(authors)

    def claim(self, syllables, input, author=None):
        try:
            db.haiku.update({'message': input}, {'$set': { 'author': author }})
            logger.info('%s has claimed the line: %s' % (author, input))
            return "%s has claimed the line: %s" % (author, input)
        except:
            return "Sorry, I don't know that line."

    def add(self, syllables, input, author=None):
        logger.info('Adding %d syllable line: %s' % (syllables, input))

        db.haiku.insert({
            'syllables': syllables,
            'message': input,
            'author': author,
        })

        return random.choice(self.add_acks)

    def add_use(self, syllables, input, author=None):
        """
        Stores a poem input and uses it in the response
        """
        self.add(syllables, input, author=author)
        return self.use(syllables, input)

    def use(self, syllables, input):
        """
        Uses input in a poem without storing it
        """
        poem = self.make_poem()

        if syllables == 5 and input not in poem:
            which = random.choice([0, 2])
            poem[which] = input
        elif syllables == 7:
            poem[1] = input

        return poem

    def remove(self, syllables, input):
        logger.info('Removing %s syllable line: %s' % (syllables, input))

        db.haiku.remove({
            'syllables': syllables,
            'message': input
        })

        return random.choice(self.delete_acks)

    def fix_repitition(self, poem, about=None, start=0, check=-1, syllables=5):
        """
        If line ``check`` repeats line ``check``, try to get a random line
        a second time, falling back to ignoring abouts
        """
        if poem[start] == poem[check]:
            repl = self.get_random_line(syllables, about)

            if repl == poem[start]:
                poem[check] = self.get_random_line(syllables)
            else:
                poem[check] = repl

        return poem

    def make_poem(self, about=None):
        poem = [
            self.get_random_line(5, about),
            self.get_random_line(7, about),
            self.get_random_line(5, about)
        ]

        if not all(poem):
            return None

        if about is not None:
            return self.fix_repitition(poem, about=about)
        else:
            return poem
