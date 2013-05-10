import random
import time

from datetime import datetime

import pytz

from helga.db import db
from helga.extensions.base import (ContextualExtension,
                                   CommandExtension)
from helga.log import setup_logger


logger = setup_logger(__name__)


class FactExtension(CommandExtension, ContextualExtension):

    NAME = 'facts'

    # contextual
    context = r'^([\w]+)\?$'
    allow_many = False
    response_fmt = '%(response)s'

    # commands
    usage = '[BOTNICK] forget <thing> | <thing> (is|are) [REPLY] (INPUT ...)'

    def should_handle_message(self, opts, message):
        # If we match 'forget', see what super() says about it
        if opts and opts['forget']:
            return super(FactExtension, self).should_handle_message(opts, message)

        # Otherwise, if we have something, we should handle it
        elif opts:
            return True

        # Nope
        else:
            return False

    def process(self, message):
        # Try to contextualize
        self.contextualize(message)

        if message.has_response:
            return

        # Try to handle commands
        opts = self.parse_command(message)

        if self.should_handle_message(opts, message):
            self.handle_message(opts, message)

    def handle_message(self, opts, message):
        if opts['forget']:
            message.response = self.remove_fact(opts['<thing>'].lower())
        elif opts['is'] or opts['are']:
            if opts['INPUT'][0] == '<reply>':
                # Weird case where <reply> is part of the input?
                is_reply = True
                opts['INPUT'] = opts['INPUT'][1:]
            else:
                is_reply = opts['REPLY'] == '<reply>'

            # We have to add matched reply thing to input because of how it matches
            if not is_reply:
                opts['INPUT'].insert(0, opts['REPLY'])

            term = opts['<thing>'].lower()

            fact = ' '.join(opts['INPUT']) if is_reply else message.message

            message.response = self.add_fact(term, fact, message.from_nick)

    def transform_match(self, match):
        return self.show_fact(match.lower())

    def show_fact(self, term):
        logger.info('Showing fact %s' % term)
        record = db.facts.find_one({'term': term})

        if record is not None:
            if 'set_date' in record:
                # Eastern time
                timestamp = datetime.fromtimestamp(record['set_date'], tz=pytz.timezone('US/Eastern'))
                formatted_dt = datetime.strftime(timestamp, '%m/%d/%Y %I:%M%p')
                set_on = ' on %s' % formatted_dt
            else:
                set_on = ''

            return '%s (%s%s)' % (record['fact'], record['set_by'], set_on)

    def add_fact(self, term, fact, nick='nobody'):
        logger.info('Adding new fact %s: %s' % (term, fact))

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
