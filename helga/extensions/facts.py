import random
import re
import time

from datetime import datetime

from helga.db import db
from helga.extensions.base import (ContextualExtension,
                                   CommandExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class FactExtension(CommandExtension, ContextualExtension):

    # contextual
    context = r'^([\w]+)\?$'
    allow_many = False
    response_fmt = '%(response)s'

    # commands
    usage = '([BOTNICK] forget <thing> | <thing> (is|are) [REPLY] (INPUT ...))'

    def should_handle_message(self, opts, is_public):
        # If we match 'forget', see what super() says about it
        if opts and opts['forget']:
            return super(FactExtension, self).should_handle_message(opts, is_public)

        # Otherwise, if we have something, we should handle it
        elif opts:
            return True

        # Nope
        else:
            return False

    def dispatch(self, nick, channel, message, is_public):
        # Try to contextualize
        response = self.contextualize(message)

        if response:
            return response

        # Try to handle commands
        opts = self.parse_command(message)

        if not self.should_handle_message(opts, is_public):
            return None

        return self.handle_message(opts, nick, channel, message, is_public)

    def handle_message(self, opts, nick, channel, message, is_public):
        if opts['forget']:
            return self.remove_fact(opts['<thing>'].lower())
        elif opts['is'] or opts['are']:
            is_reply = opts['REPLY'] and opts['REPLY'] == '<reply>'

            # We have to add matched reply thing to input because of how it matches
            if opts['REPLY'] and not is_reply:
                opts['INPUT'].insert(0, opts['REPLY'])

            term = opts['<thing>'].lower()

            if is_reply:
                fact = ' '.join(opts['INPUT'])
            else:
                # Everything
                fact = message

            return self.add_fact(term, fact, nick)

    def transform_match(self, match):
        return self.show_fact(match.lower())

    def show_fact(self, term):
        logger.info('Showing fact %s' % term)
        record = db.facts.find_one({'term': term})

        if record is not None:
            if 'set_date' in record:
                formatted_dt = datetime.strftime(datetime.fromtimestamp(record['set_date']),
                                                 '%m/%d/%Y %I:%M%p')
                set_on = ' on %s' % formatted_dt
            else:
                set_on = ''

            return '%s (%s%s)' % (record['fact'], record['set_by'], set_on)

    def add_fact(self, term, fact, nick='nobody'):
        logger.info('Adding new fact %s' % term)

        if not db.facts.find({'term': term}).count():
            db.facts.insert({
                'term': term.lower(),
                'fact': fact,
                'set_by': nick,
                'set_date': time.time()
            })
            db.facts.ensure_index('term')

    def remove_fact(self, term):
        logger.info('Removing fact %s' % term)
        db.facts.remove({'term': term})

        return random.choice(self.delete_acks)
