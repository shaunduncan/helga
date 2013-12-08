# -*- coding: utf8 -*-
from helga.plugins import match


@match(r'^olga')
def no_more_olga(client, channel, nick, message, matches):
    """
    Make sure people are talking to helga and not olga
    """
    return '{0}, you should talk to me instead. Olga is no more'.format(nick)
