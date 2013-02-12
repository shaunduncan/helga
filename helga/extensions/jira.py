import logging
import random
import re

from helga import settings
from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(logging.getLogger(__name__))


class JiraExtension(HelgaExtension):

    add_acks = HelgaExtension.acks + (
        'added',
        'consider it done',
    )

    delete_acks = HelgaExtension.acks + (
        'deleted',
        'nuking from orbit',
        'consider it done',
    )

    _pub_cmd_fmt = '^%s jira %s ([a-zA-Z0-9]+)$'
    _priv_cmd_fmt = '^(%s )?jira %s ([a-zA-Z0-9]+)$'

    def __init__(self):
        self.jira_pats = set(item['re'] for item in db.jira.find())

    def handle_add(self, bot, message, is_public):
        if is_public:
            pat = self._pub_cmd_fmt % (bot.nick, 'add_re')
        else:
            pat = self._priv_cmd_fmt % (bot.nick, 'add_re')

        try:
            all = re.findall(pat, message)
            new_re = all[0] if is_public else all[0][1]
        except IndexError:
            return

        if new_re not in self.jira_pats:
            logger.info('Adding new JIRA ticket RE: %s' % new_re)

            self.jira_pats.add(new_re)
            db.jira.insert({'re': new_re})
        else:
            logger.info('JIRA ticket RE already exists: %s' % new_re)

        return '%(nick)s, ' + random.choice(self.add_acks)

    def handle_remove(self, bot, message, is_public):
        if is_public:
            pat = self._pub_cmd_fmt % (bot.nick, 'remove_re')
        else:
            pat = self._priv_cmd_fmt % (bot.nick, 'remove_re')

        try:
            all = re.findall(pat, message)
            rem_re = all[0] if is_public else all[0][1]
        except IndexError:
            return

        logger.info('Removing JIRA ticket RE: %s' % rem_re)
        self.jira_pats.discard(rem_re)
        db.jira.remove({'re': rem_re})

        return '%(nick)s, ' + random.choice(self.delete_acks)

    def contextualize(self, message):
        """
        Turns the whole MYPROJ-123 into JIRA urls
        """
        all_pat = r'((%s)-[0-9]+)' % '|'.join(self.jira_pats)
        jira_urls = []

        logger.info('Checking this regex: %s' % all_pat)

        for match in re.findall(all_pat, message, re.I):
            jira_urls.append(settings.JIRA_URL % {'ticket': match[0]})

        if jira_urls:
            return '%(nick)s might be talking about: ' + ', '.join(jira_urls)

    def dispatch(self, bot, nick, channel, message, is_public):
        responses = []

        # First allow for updating ticket re
        responses.append(self.handle_add(bot, message, is_public))

        # Handle removing
        responses.append(self.handle_remove(bot, message, is_public))

        # Handle contextual "this looks like a ticket"
        if not all(responses):
            responses.append(self.contextualize(message))

        return responses
