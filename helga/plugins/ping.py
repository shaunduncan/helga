from helga.plugins import command


@command('ping', help='A very simple PING plugin. Response with pong. Usage: helga ping')
def ping(*args, **kwargs):
    """
    Respond to a ping with a pong
    """
    return u'pong'
