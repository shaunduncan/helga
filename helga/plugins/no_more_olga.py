# -*- coding: utf8 -*-
import random
import re

from helga import settings
from helga.extensions.oneliner import OneLinerExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


def imgur(image):
    return 'http://i.imgur.com/%s.gif' % image


class NoMoreOlgaExtension(OneLinerExtension):
    """
    Just tell people not to talk to olga
    """

    NAME = 'no_more_olga'

    responses = {
        # Direct text responses
        r'^olga': ("%(nick)s, you should talk to me instead. Olga is no more",),
    }
