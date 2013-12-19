import random
import re

import requests
import smokesignal

from BeautifulSoup import BeautifulSoup
from requests.auth import HTTPBasicAuth
from twisted.internet import reactor

from helga import log, settings
from helga.db import db
from helga.plugins import command, match, ACKS, ResponseNotReady


logger = log.getLogger(__name__)


# These are initialized on client signon
JIRA_PATTERNS = set()


@smokesignal.on('signon')
def init_jira_patterns(*args, **kwargs):
    """
    Signal callback for IRC signon. This pulls down and caches all the stored
    JIRA ticket patterns so we don't have to do it on every message received
    """
    global JIRA_PATTERNS

    if db is None:
        logger.warning('Cannot initialize JIRA patterns. No database connection')

    JIRA_PATTERNS = set(item['re'] for item in db.jira.find())


def find_jira_numbers(message):
    """
    Finds all jira ticket numbers in a message. This will ignore any that already
    appear in a URL
    """
    global JIRA_PATTERNS

    pat = r'(https?://.*?)?(({0})-\d+)($|[\s\W]+)'.format('|'.join(JIRA_PATTERNS))
    tickets = []
    for match in re.findall(pat, message, re.IGNORECASE):
        # if match[0] is not empty, the ticket is in a URL. Ignore it
        if match[0]:
            continue
        tickets.append(match[1])

    return tickets


def add_re(pattern):
    """
    Adds a ticket pattern from the database and local cache
    """
    global JIRA_PATTERNS

    if pattern not in JIRA_PATTERNS:
        logger.info('Adding new JIRA ticket RE: {0}'.format(pattern))
        JIRA_PATTERNS.add(pattern)
        re_doc = {'re': pattern}

        # Store in DB
        if not db.jira.find(re_doc).count():
            db.jira.insert(re_doc)
    else:
        logger.info('JIRA ticket RE already exists: {0}'.format(pattern))

    return random.choice(ACKS)


def remove_re(pattern):
    """
    Removes a ticket pattern from the database and local cache
    """
    global JIRA_PATTERNS

    logger.info('Removing JIRA ticket RE: {0}'.format(pattern))
    JIRA_PATTERNS.discard(pattern)
    db.jira.remove({'re': pattern})

    return random.choice(ACKS)


def jira_command(client, channel, nick, message, cmd, args):
    """
    Command handler for the jira plugin
    """
    try:
        subcmd, pattern = args[:2]
    except ValueError:
        return None

    if subcmd == 'add_re':
        return add_re(pattern)

    if subcmd == 'remove_re':
        return remove_re(pattern)

    return None


def _soup_desc(ticket, url, auth=None):
    resp = requests.get(url, auth=auth)

    try:
        resp.raise_for_status()
    except:
        logger.error("Error getting JIRA ticket {0}. Status {1}".format(url, resp.status_code))
        return

    try:
        soup = BeautifulSoup(resp.content)
        title = soup.find('h2', attrs={'id': 'issue_header_summary'}).text
        return '[{0}] {1} ({2})'.format(ticket.upper(), title, url)
    except:
        return '[{0}] {1}'.format(ticket.upper(), url)


def _rest_desc(ticket, url, auth=None):
    resp = requests.get(settings.JIRA_REST_API.format(ticket=ticket), auth=auth)

    try:
        resp.raise_for_status()
    except:
        logger.error("Error getting JIRA ticket {0}. Status {1}".format(ticket, resp.status_code))
        return

    try:
        return '[{0}] {1} ({2})'.format(ticket.upper(), resp.json()['fields']['summary'], url)
    except:
        return '[{0}] {1}'.format(ticket.upper(), url)


def jira_full_descriptions(client, channel, urls):
    """
    Meant to be run asynchronously because it uses the network
    """
    descriptions = []
    fn = _soup_desc if getattr(settings, 'JIRA_REST_API', '') == '' else _rest_desc

    user_pass = getattr(settings, 'JIRA_AUTH', ('', ''))
    if all(user_pass):
        auth = HTTPBasicAuth(*user_pass)
    else:
        auth = None

    for ticket, url in urls.iteritems():
        desc = fn(ticket, url, auth)
        if desc is not None:
            descriptions.append(desc)

    if descriptions:
        client.msg(channel, '\n'.join(descriptions))


def jira_match(client, channel, nick, message, matches):
    full_urls = dict(map(lambda s: (s, settings.JIRA_URL.format(ticket=s)), matches))

    if not getattr(settings, 'JIRA_SHOW_FULL_DESCRIPTION', True):
        return '{0} might be talking about JIRA ticket: {1}'.format(nick, ', '.join(full_urls.values()))

    # Otherwise, do the fetching with a deferred
    reactor.callLater(0, jira_full_descriptions, client, channel, full_urls)
    raise ResponseNotReady


@match(find_jira_numbers)
@command('jira', help="Add or remove jira ticket patterns, excludeing numbers."
                      "Usage: helga jira (add_re|remove_re) <pattern>")
def jira(client, channel, nick, message, *args):
    """
    A plugin for showing URLs to JIRA ticket numbers. This is both a command to add or remove
    patterns, and a match to automatically show them. The match requires a setting JIRA_URL
    which must contain a ``{ticket}`` substring. For example, ``http://localhost/{ticket}``.

    The command takes a pattern as an argument, minus any numbers. For example, if there are JIRA
    tickets like FOOBAR-1, FOOBAR-2, and FOOBAR-3. Then you could manage the pattern via::

        helga jira add_re FOOBAR
        helga jira remove_re FOOBAR

    Ticket numbers are automatically detected.
    """
    if len(args) == 2:
        fn = jira_command
    else:
        fn = jira_match
    return fn(client, channel, nick, message, *args)
