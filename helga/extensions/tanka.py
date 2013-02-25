import random

from helga.db import db
from helga.extensions.haiku import HaikuExtension


class TankaExtension(HaikuExtension):

    command_pat = r'^(%s )?tanka( (add|add_use|remove|tweet_last) (fives|sevens) (.+))?$'

    def add_use_line(self, num_syllables, message):
        self.add_line(num_syllables, message)
        poem = self.make_poem()

        if num_syllables == 5 and message not in poem:
            which = random.choice([0, 2])
            poem[which] = message
        elif num_syllables == 7 and message not in poem:
            which = random.choice([1, 3, 4])
            poem[which] = message

        return poem

    def make_poem(self):
        poem = super(TankaExtension, self).make_poem()

        if poem is None:
            return None

        sevens_qs = db.haiku.find({'syllables': 7})
        randsevens = sevens_qs.count() - 1

        poem.extend([
            sevens_qs.sort('random')[random.randint(0, randsevens)]['message'],
            sevens_qs.sort('random')[random.randint(0, randsevens)]['message'],
        ])

        return poem
