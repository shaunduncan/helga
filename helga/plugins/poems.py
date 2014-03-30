import random
import re

from collections import defaultdict

from twisted.internet import reactor

from helga import log
from helga.db import db
from helga.plugins import command, random_ack, ResponseNotReady
from helga.util.twitter import tweet as send_tweet


logger = log.getLogger(__name__)


SYLLABLES_TO_INT = {
    'fives': 5,
    'sevens': 7,
}

last_poem = defaultdict(list)


@command('haiku', aliases=['tanka'],
         help="Usage: helga (haiku|tanka) [blame|tweet|about <thing>|by <author_nick>|"
              "(add|add_use|use|remove|claim) (fives|sevens) (INPUT ...)]")
def poems(client, channel, nick, message, cmd, args):
    global last_poem

    # Just a poem
    if not args:
        poem = make_poem(poem_type=cmd)
        last_poem[channel] = poem
        return poem

    subcmd = args[0]

    # Other commands
    if subcmd in ('about', 'by'):
        poem = make_poem(**{'poem_type': cmd, subcmd: ' '.join(args[1:])})
        last_poem[channel] = poem
        return poem
    elif subcmd == 'blame':
        return blame(channel, requested_by=nick, default_author=client.nickname)
    elif subcmd == 'tweet':
        reactor.callLater(0, tweet, client, channel, nick)
        raise ResponseNotReady
    else:
        logger.info('Running subcmd: "{0}"'.format(subcmd))
        num_syllables = SYLLABLES_TO_INT[args[1]]
        input = ' '.join(args[2:])

        if subcmd == 'add':
            return add(num_syllables, input, nick)
        elif subcmd == 'add_use':
            poem = add_use(num_syllables, input, nick)
            last_poem[channel] = poem
            return poem
        elif subcmd == 'use':
            poem = use(num_syllables, input)
            last_poem[channel] = poem
            return poem
        elif subcmd == 'remove':
            return remove(num_syllables, input)
        elif subcmd == 'claim':
            return claim(num_syllables, input, nick)


def fix_repitition(poem, about=None, by=None, start=0, check=-1, syllables=5):
    """
    If line ``check`` repeats line ``start``, try to get a random line
    a second time, falling back to ignoring abouts

    :param poem: a list of strings
    :param about: any string or regex will search for a line with this pattern
    :param by: string of user nick to use to search for haiku lines
    :param start: start index (leftmost) of poem list
    :param check: index of poem list that will be replaced if it matches ``start``
    :param syllables: number of syllables of the poem at ``start`` and ``check``
    """
    if poem[start] == poem[check]:
        repl = get_random_line(syllables, about, by)

        if repl == poem[start]:
            poem[check] = get_random_line(syllables)
        else:
            poem[check] = repl

    return poem


def get_random_line(syllables, about=None, by=None):
    """
    Returns a single random line with the given number of syllables.
    Optionally will find lines containing a keyword or by an author.
    If no entries are found with that keyword or by that author,
    we just return a random line.

    :param syllables: integer number of syllables, 5 or 7
    :param about: any string or regex will search for a line with this pattern
    :param by: string of user nick to use to search for haiku lines
    """
    query = {'syllables': syllables}

    if by:
        query.update({'author': {'$regex': re.compile(by, re.I)}})

    if about:
        query.update({'message': {'$regex': re.compile(about, re.I)}})

    qs = db.haiku.find(query)
    num_rows = qs.count()

    if num_rows == 0:
        if about or by:
            # If no results using either an author or general search
            return get_random_line(syllables)
        else:
            # Bail
            return None

    skip = random.randint(0, num_rows - 1)

    # Bleh, this is how we randomly grab one
    return str(qs.limit(-1).skip(skip).next()['message'])


def make_poem(about=None, by=None, poem_type='haiku'):
    """
    Makes a haiku poem
    """
    poem = [
        get_random_line(5, about, by),
        get_random_line(7, about, by),
        get_random_line(5, about, by)
    ]

    if not all(poem):
        return None

    fixrep_kw = {}
    if about is not None:
        fixrep_kw['about'] = about
    elif by is not None:
        fixrep_kw['by'] = by

    poem = fix_repitition(poem, **fixrep_kw)

    if random.choice((0, 1)) == 1:
        # Reverse so that if only one 5-line matches an about/by,
        # haiku will sometimes end with that line.
        poem.reverse()

    if poem_type == 'tanka':
        poem.extend([
            get_random_line(7, about, by),
            get_random_line(7, about, by)
        ])

        fixrep_kw.update({'start': 3, 'syllables': 7})
        poem = fix_repitition(poem, **fixrep_kw)

    return poem


def add(syllables, input, author=None):
    logger.info('Adding {0} syllable line: {1}'.format(syllables, input))
    db.haiku.insert({
        'syllables': syllables,
        'message': input,
        'author': author,
    })
    return random_ack()


def add_use(syllables, input, author=None):
    """
    Stores a poem input and uses it in the response
    """
    add(syllables, input, author=author)
    return use(syllables, input)


def use(syllables, input, poem_type='haiku'):
    """
    Uses input in a poem without storing it
    """
    poem = make_poem(poem_type=poem_type)

    # Already used
    if input in poem:
        return poem

    repl_idx = None

    if syllables == 5:
        repl_idx = random.choice([0, 2])
    elif syllables == 7:
        repl_idx = random.choice([1] if poem_type == 'haiku' else [1, 3, 4])

    if repl_idx is not None:
        poem[repl_idx] = input

    return poem


def remove(syllables, input):
    logger.info('Removing {0} syllable line: {1}'.format(syllables, input))
    db.haiku.remove({'syllables': syllables, 'message': input})
    return random_ack()


def claim(syllables, input, author=None):
    try:
        db.haiku.update({'message': input}, {'$set': {'author': author}})
        logger.info('{0} has claimed the line: {1}'.format(author, input))
        return "{0} has claimed the line: {1}".format(author, input)
    except:
        return "Sorry, I don't know that line."


def tweet(client, channel, requested_by):
    global last_poem
    last = last_poem[channel]

    if not last:
        msg = "{0}, why don't you try making one first".format(requested_by)
        client.msg(channel, msg)
        return

    resp = send_tweet('\n'.join(last))

    if not resp:
        msg = "{0}, that probably did not work :(".format(requested_by)
        client.msg(channel, msg)
    else:
        # This will keep it from over tweeting
        del last_poem[channel]

    client.msg(channel, resp)


def blame(channel, requested_by, default_author=''):
    """
    Show who helped make the last haiku possible
    """
    global last_poem
    last = last_poem[channel]

    if not last:
        return "{0}, why don't you try making one first".format(requested_by)

    authors = []

    for line in last:
        try:
            rec = db.haiku.find_one({'message': line})
        except:
            authors.append(default_author)
        else:
            authors.append(rec.get('author', None) or default_author)

    return "The last poem was brought to you by (in order): {0}".format(', '.join(authors))
