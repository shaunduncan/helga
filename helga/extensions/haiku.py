import random
import re

from helga import settings
from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger
from helga.util.twitter import tweet


logger = setup_logger(__name__)


class HaikuExtension(HelgaExtension):

    command_pat = r'^(%s )?haiku( (tweet_last|(add|add_use|remove) (fives|sevens) (.+)))?$'

    command_map = {
        'add': 'add_line',
        'add_use': 'add_use_line',
        'remove': 'remove_line',
    }

    syllables = {
        'fives': 5,
        'sevens': 7,
    }

    last = {}

    def tweet_last(self, channel):
        # *args here because we call it like add_line/add_use_line/remove_line
        # TODO: There should be a twitter extension to do this bit
        if channel not in self.last:
            return "%(nick)s, why don't you try making one first?"

        # fives / sevens / fives
        resp = tweet('\r'.join(self.last[channel]))

        # This will keep it from over tweeting
        del self.last[channel]

        if not resp:
            resp = '%(nick)s that probably did not work'

        return resp

    def add_line(self, num_syllables, message):
        logger.info('Adding %d syllable line: %s' % (num_syllables, message))

        db.haiku.insert({
            'syllables': num_syllables,
            'message': message,
            'random': random.random()
        })

        return random.choice(self.add_acks)

    def add_use_line(self, num_syllables, message):
        self.add_line(num_syllables, message)
        poem = self.make_poem()

        if num_syllables == 5 and message not in poem:
            which = random.choice([0, 2])
            poem[which] = message
        elif num_syllables == 7:
            poem[1] = message

        return poem

    def remove_line(self, num_syllables, message):
        logger.info('Removing %s syllable line: %s' % (num_syllables, message))

        db.haiku.remove({
            'syllables': num_syllables,
            'message': message
        })

        return '%(nick)s, ' + random.choice(self.delete_acks)

    def make_poem(self):
        fives_qs = db.haiku.find({'syllables': 5})
        sevens_qs = db.haiku.find({'syllables': 7})

        randfives = fives_qs.count() - 1
        randsevens = sevens_qs.count() - 1

        if randfives < 0 or randsevens < 0:
            return None

        int1 = random.randint(0, randfives)
        int2 = random.randint(0, randsevens)
        int3 = random.randint(0, randfives)

        return map(str, [
            fives_qs.sort('random')[int1]['message'],
            sevens_qs.sort('random')[int2]['message'],
            fives_qs.sort('random')[int3]['message'],
        ])

    def parse_message(self, message, is_public):
        parts = re.findall(self.command_pat % self.bot.nick, message)

        if not parts or (is_public and not parts[0][0]):
            raise Exception("Don't do anything")

        # command, syllables, line
        parts = parts[0]
        return parts[-3] or parts[-4], parts[-2], parts[-1]

    def dispatch(self, nick, channel, message, is_public):
        last_chan = channel if is_public else nick

        try:
            command, syllables, msg_parts = self.parse_message(message, is_public)
        except:
            # This only happens when we don't match anything
            return None

        if not command:
            resp = self.make_poem()
        elif command == 'tweet_last':
            resp = self.tweet_last(last_chan)
        else:
            num_syllables = self.syllables[syllables]  # We only match fives/sevens
            call_me_maybe = getattr(self, self.command_map[command])
            resp = call_me_maybe(num_syllables, msg_parts)

        # Store last poem if it's a poem
        if isinstance(resp, list):
            self.last[last_chan] = resp

        return resp
