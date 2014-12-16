import datetime
import re

import pymongo

from helga import settings
from helga.db import db
from helga.plugins import command


def _do_search(channel, term=None, nick=None, limit=None):
    """
    Search logs, optionally limited by a nick or using a search term
    """
    spec = [{'channel': channel}]
    limit = limit or settings.CHANNEL_LOGGING_DB_SEARCH_LIMIT
    about_search = u'Last {0} logged messages for {1}'.format(limit, channel)

    if term is not None:
        spec.append({'message':  {'$regex': re.compile(term, re.I)}})
        about_search = u'{0} (term: {1})'.format(about_search, term)

    if nick is not None:
        spec.append({'nick': {'$regex': re.compile(nick, re.I)}})
        about_search = u'{0} (by: {1})'.format(about_search, nick)

    yield about_search

    sort_order = [('created', pymongo.DESCENDING)]
    qs = db.channel_logs.find({'$and': spec}, limit=limit, sort=sort_order)

    if qs.count() == 0:
        yield u'No results found'
        raise StopIteration

    for rec in reversed(list(qs)):
        dt = datetime.datetime.fromtimestamp(rec['created'])
        rec['created'] = dt.strftime('%m/%d/%Y %H:%M UTC')
        yield u'[{created}][{channel}] {nick} - {message}'.format(**rec)


@command('log', aliases=['logs'], help='Query helga channel logs. Usage: helga logs '
         '(search <term>|search_by <nick> <term>|recent|recent_by <nick>) [on <channel>]')
def logger(client, channel, nick, message, cmd, args):
    if not settings.CHANNEL_LOGGING_DB:
        return u'Log searching is only available with CHANNEL_LOGGING_DB enabled'

    subcmd = args.pop(0)

    if subcmd not in ('search', 'search_by', 'recent', 'recent_by'):
        return

    search_channel = None
    search_term = None
    search_nick = None

    # What channel should we look at
    if re.match(r'^on #\w+$', ' '.join(args[-2:])):
        search_channel = args.pop()
        args.pop()  # Eliminate 'on'
    else:
        search_channel = channel

    # Handle nick limited searches
    if subcmd in ('search_by', 'recent_by'):
        search_nick = args.pop(0)
        subcmd = subcmd[:-3]

    if subcmd == 'search':
        search_term = ' '.join(args)

    if channel != nick:
        client.me(channel, u'whispers to {0}'.format(nick))

    response = _do_search(channel=search_channel, term=search_term, nick=search_nick)
    client.msg(nick, u'\n'.join(response))
