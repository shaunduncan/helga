import random
import re
import time

from datetime import datetime

from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class FactExtension(HelgaExtension):

    patterns = {
        'add': r'^([\w]+) (is|are) (<reply> )?([\w]+)$',
        'remove': r'^(%s )?forget ([\w]+)$',
        'get': r'^([\w]+)\?$',
    }

    def add_fact(self, message, nick='nobody'):
        matches = re.findall(self.patterns['add'], message, re.I)

        if not matches:
            return

        term, isare, is_reply, fact = matches[0]
        term = term.lower()

        # The whole shebang
        if not is_reply:
            fact = message

        logger.info('Adding new fact %s' % term)

        if not db.facts.find({'term': term}).count():
            db.facts.insert({
                'term': term.lower(),
                'fact': fact,
                'set_by': nick,
                'set_date': time.time()
            })
            db.facts.ensure_index('term')

    def remove_fact(self, message, is_public):
        # Of the form: helga forget foo
        matches = re.findall(self.patterns['remove'] % self.bot.nick, message, re.I)

        if not matches or (is_public and matches[0][0] != self.bot.nick):
            return

        botnick, term = matches[0]

        logger.info('Removing fact %s' % term)

        db.facts.remove({'term': term})

        return random.choice(self.delete_acks)

    def show_fact(self, message):
        matches = re.findall(self.patterns['get'], message, re.I)

        if not matches:
            return

        term = matches[0].lower()

        record = db.facts.find_one({'term': term})
        logger.info('Showing fact %s' % term)

        if record is not None:
            if 'set_date' in record:
                formatted_dt = datetime.strftime(datetime.fromtimestamp(record['set_date']),
                                                 '%m/%d/%Y %I:%M%p')
                set_on = ' on %s' % formatted_dt
            else:
                set_on = ''

            return '%s (%s%s)' % (record['fact'], record['set_by'], set_on)

    def dispatch(self, nick, channel, message, is_public):
        # Chain add/remove/show and return the first response
        return (
            self.add_fact(message, nick) or
            self.remove_fact(message, is_public) or
            self.show_fact(message)
        )
