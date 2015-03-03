from helga.plugins import command


@command('ping', help='A very simple PING plugin. Response with pong. Usage: helga ping')
def ping(client, channel, nick, message, cmd, args):
    return u'pong'
