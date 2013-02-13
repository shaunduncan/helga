import re
import urllib2

from helga.db import db
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class BullshitExtension(HelgaExtension):
    """
    Responds will bullshit/corporate-speak things
    """

    def dispatch(self, bot, nick, channel, message, is_public):
        # FIXME
        pass
