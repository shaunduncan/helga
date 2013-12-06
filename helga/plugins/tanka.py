import random

from helga.extensions.haiku import HaikuExtension


class TankaExtension(HaikuExtension):

    NAME = 'tanka'

    usage = '[BOTNICK] tanka [blame|tweet|about (<thing> ...)|by (<author_nick> ...)|(add|add_use|use|remove|claim) (fives|sevens) (INPUT ...)]'

    def use(self, syllables, message):
        poem = self.make_poem()

        if syllables == 5 and message not in poem:
            which = random.choice([0, 2])
            poem[which] = message
        elif syllables == 7 and message not in poem:
            which = random.choice([1, 3, 4])
            poem[which] = message

        return poem

    def make_poem(self, about=None, by=None):
        poem = super(TankaExtension, self).make_poem(about=about, by=by)

        if poem is None:
            return None

        poem.extend([
            self.get_random_line(7, about, by),
            self.get_random_line(7, about, by)
        ])

        if about is not None:
            return self.fix_repitition(poem, about=about, start=4, syllables=7)
        elif by is not None:
            return self.fix_repitition(poem, by=by, start=4, syllables=7)
        else:
            return poem
