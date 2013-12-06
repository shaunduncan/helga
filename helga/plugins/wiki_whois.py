from helga import settings
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class WikiWhoisExtension(CommandExtension):
    """
    A simple pattern substitution for making a URL containing a user/nick
    """

    NAME = 'wiki_whois'

    usage = '[BOTNICK] (showme|whois|whothehellis) <nick>'

    def handle_message(self, opts, message):
        message.response = settings.WIKI_URL % {'user': opts['<nick>']}
