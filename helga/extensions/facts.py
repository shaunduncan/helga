import random
import re
import time

from datetime import datetime

from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class FactExtension(HelgaExtension):

    def add_fact(self, nick, message):
        matches = re.findall(r'^([a-z0-9]+) (is|are) (<reply> )?([\w]+)$', message, re.I)

        if not matches:
            return

        term, isare, reply, fact = matches[0]
        term = term.lower()

        # The whole shebang
        if not reply:
            fact = message

        logger.info('Adding new fact %s' % term)

        if not db.facts.find({'term': term}).count():
            db.facts.insert({
                'term': term,
                'fact': fact,
                'set_by': nick,
                'set_date': time.time()
            })
            db.facts.ensure_index('term')

    def remove_fact(self, bot, message, is_public):
        # Of the form: helga forget foo
        pat = ((r'^%s ' if is_public else r'^(%s )?') % bot.nick) + r'forget ([a-z0-9]+)$'
        matches = re.findall(pat, message, re.I)

        if not matches:
            return

        logger.info(matches)
        term = matches[0]

        # Fix for matching nick or not
        if not isinstance(term, basestring):
            term = term[-1]

        logger.info('Removing fact %s' % term)
        db.facts.remove({'term': term})
        return random.choice(self.delete_acks)

    def show_fact(self, message):
        matches = re.findall(r'^([a-z0-9]+)\?$', message, re.I)

        if not matches:
            return

        term = matches[0].lower()
        record = db.facts.find_one({'term': term})
        logger.info('Showing fact %s' % term)

        if record is not None:
            formatted_dt = datetime.strftime(datetime.fromtimestamp(record['set_date']),
                                             '%m/%d/%Y %I:%M%p')

            return '%s (%s on %s)' % (record['fact'], record['set_by'], formatted_dt)

    def dispatch(self, bot, nick, channel, message, is_public):
        # Check for adding
        response = self.handle_add(nick, message)

        # Check for removing
        if not response:
            response = self.handle_remove(bot, message, is_public)

        # Check for fact showing
        if not response:
            response = self.show_fact(message)

        return response
