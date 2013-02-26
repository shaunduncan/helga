import random
import re

from helga import settings
from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class JiraExtension(HelgaExtension):

    def __init__(self, *args, **kwargs):
        if kwargs.get('load', True):
            self.jira_pats = set(item['re'] for item in db.jira.find())
        else:
            self.jira_pats = set()

        if 'load' in kwargs:
            del kwargs['load']

        super(JiraExtension, self).__init__(*args, **kwargs)

    def get_ticket_re(self, command, message, is_public):
        if is_public:
            pat = r'^%s jira %s (.+)$'
        else:
            pat = r'^(%s )?jira %s (.+)$'

        matches = re.findall(pat % (self.bot.nick, command), message)

        if matches:
            # Public ['cmd']
            # Non-public [('nick', 'cmd')]
            return matches[0] if is_public else matches[0][1]

        return None

    def add_ticket_re(self, message, is_public):
        new_re = self.get_ticket_re('add_re', message, is_public)

        if new_re:
            if new_re not in self.jira_pats:
                logger.info('Adding new JIRA ticket RE: %s' % new_re)

                self.jira_pats.add(new_re)
                re_doc = {'re': new_re}

                # Store in DB
                if not db.jira.find(re_doc).count():
                    db.jira.insert({'re': new_re})
            else:
                logger.info('JIRA ticket RE already exists: %s' % new_re)

            return '%(nick)s, ' + random.choice(self.add_acks)

    def remove_ticket_re(self, message, is_public):
        rem_re = self.get_ticket_re('remove_re', message, is_public)

        if rem_re:
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

        logger.debug('Checking jira regex: %s' % all_pat)

        for match in re.findall(all_pat, message, re.I):
            jira_urls.append(settings.JIRA_URL % {'ticket': match[0]})

        if jira_urls:
            return '%(nick)s might be talking about: ' + ', '.join(jira_urls)

    def dispatch(self, nick, channel, message, is_public):
        # Return the first-of response
        return (
            self.add_ticket_re(message, is_public) or
            self.remove_ticket_re(message, is_public) or
            self.contextualize(message)
        )
