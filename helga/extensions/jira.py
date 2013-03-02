import random
import re

from helga import settings
from helga.db import db
from helga.extensions.base import (CommandExtension,
                                   ContextualExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class JiraExtension(CommandExtension, ContextualExtension):

    NAME = 'jira'

    usage = '[BOTNICK] jira (add_re|remove_re) <pattern>'

    allow_many = True

    def __init__(self, *args, **kwargs):
        self.jira_pats = set()
        super(JiraExtension, self).__init__(*args, **kwargs)

    @property
    def context(self):
        return r'((%s)-[0-9]+)' % '|'.join(self.jira_pats)

    def on(self, event, *args, **kwargs):
        if event == 'signon':
            self.jira_pats = set(item['re'] for item in db.jira.find())

    def transform_match(self, match):
        return settings.JIRA_URL % {'ticket': match[0]}

    def handle_message(self, opts, message):
        if opts['add_re']:
            message.response = self.add_re(opts['<pattern>'])
        elif opts['remove_re']:
            message.response = self.remove_re(opts['<pattern>'])

    def add_re(self, pattern):
        if pattern not in self.jira_pats:
            logger.info('Adding new JIRA ticket RE: %s' % pattern)

            self.jira_pats.add(pattern)
            re_doc = {'re': pattern}

            # Store in DB
            if not db.jira.find(re_doc).count():
                db.jira.insert(re_doc)
        else:
            logger.info('JIRA ticket RE already exists: %s' % pattern)

        return '%(nick)s, ' + random.choice(self.add_acks)

    def remove_re(self, pattern):
        logger.info('Removing JIRA ticket RE: %s' % pattern)
        self.jira_pats.discard(pattern)
        db.jira.remove({'re': pattern})

        return '%(nick)s, ' + random.choice(self.delete_acks)

    def process(self, message):
        # Try to contextualize
        self.contextualize(message)

        if message.has_response:
            return

        # Try to handle commands
        opts = self.parse_command(message)

        if self.should_handle_message(opts, message):
            self.handle_message(opts, message)
