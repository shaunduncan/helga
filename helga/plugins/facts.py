import random
import re
import time

from datetime import datetime

import pytz

from helga import log, settings
from helga.db import db
from helga.plugins import command, match, ACKS


logger = log.getLogger(__name__)


def term_regex(term):
    """
    Returns a case-insensitive regex for searching terms
    """
    return re.compile('^{0}$'.format(re.escape(term)), re.IGNORECASE)


def show_fact(term):
    """
    Shows a fact stored for a given term, using a case-insensitive search.
    If a fact has an author, it will be shown. If it has a timestamp, that will
    also be shown.
    """
    logger.info('Showing fact {0}'.format(term))
    record = db.facts.find_one({'term': term_regex(term)})

    if record is None:
        return None

    # If it isn't authored
    if not record.get('set_by', ''):
        return record['fact']

    if 'set_date' not in record:
        return '{fact} ({set_by})'.format(**record)

    # Otherwise, do normal formatting
    tz = getattr(settings, 'TIMEZONE', 'US/Eastern')
    try:
        timestamp = datetime.fromtimestamp(record['set_date'], tz=pytz.timezone(tz))
    except TypeError:
        timestamp = record['set_date'].replace(tzinfo=pytz.timezone(tz))
    record['fmt_dt'] = datetime.strftime(timestamp, '%m/%d/%Y %I:%M%p')

    return '{fact} ({set_by} on {fmt_dt})'.format(**record)


def add_fact(term, fact, author=''):
    """
    Records a new fact with a given term. Optionally can set an author
    """
    logger.info('Adding new fact {0}: {1}'.format(term, fact))

    if not db.facts.find({'term': term_regex(term)}).count():
        db.facts.insert({
            'term': term,
            'fact': fact,
            'set_by': author,
            'set_date': time.time()
        })
        db.facts.ensure_index('term')


def forget_fact(term):
    """
    Forgets a fact by removing it from the database
    """
    logger.info('Removing fact {0}'.format(term))
    db.facts.remove({'term': term_regex(term)})
    return random.choice(ACKS)


def facts_command(client, channel, nick, message, cmd, args):
    if cmd == 'forget':
        return forget_fact(' '.join(args))


def facts_match(client, channel, nick, message, found):
    parts = found[0]

    # Like: foo?
    if isinstance(parts, basestring):
        return show_fact(parts)

    # Allow customizing facts to be non-automatic and work more like commands
    if getattr(settings, 'FACTS_REQUIRE_NICKNAME', False):
        try:
            nonick = re.findall(r'^{0}\W*\s(.*)$'.format(client.nickname), parts[0])[0]
        except IndexError:
            logger.debug('Facts require the current bot nick. Ignoring: {0}'.format(parts[0]))
            return None
        else:
            parts = [nonick] + list(parts[1:])

    if parts[2].strip() == '<reply>':
        author = ''
        fact = parts[-1]
    else:
        # This nasty join is to ignore the empty part for <reply>
        author = nick
        fact = ' '.join(parts[:2] + parts[-1:])

    return add_fact(parts[0], fact, author)


@command('forget', help='Forget a stored fact. Usage: <botnick> forget foo')
@match(r'^(.*?) (is|are)( <reply>)? (.+)$')  # Storing facts
@match(r'^(.*)\?$')  # Showing facts
def facts(client, channel, nick, message, *args):
    """
    A plugin for helga to automatically remember important things. Unless specified
    by the setting ``FACTS_REQUIRE_NICKNAME``, facts are automatically stored when
    a user says: ``something is something else``. Otherwise, facts must be explicitly
    added: ``helga something is something else``.

    Response format is, by default, the full message that was sent, including an author
    and timestamp. However, if a user specifies the string '<reply>' in their message,
    then only the words that follow '<reply>' will be returned in the response.

    For example::

        <sduncan> foo is bar
        <sduncan> foo?
        <helga> foo is bar (sduncan on 12/02/2013)

    Or::

        <sduncan> foo is <reply> bar
        <sduncan> foo?
        <helga> bar (sduncan on 12/02/2013)

    To remove a fact, you must ask specifically using the ``forget`` command::

        <sduncan> helga forget foo
        <helga> forgotten
    """
    if len(args) == 2:
        return facts_command(client, channel, nick, message, *args)

    # Anything else is a match
    return facts_match(client, channel, nick, message, args[0])
