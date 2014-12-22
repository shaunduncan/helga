from helga import settings
from helga.plugins import command, preprocessor


ignored = set()


def _do_preprocess(channel, nick, message):
    global ignored

    if nick in ignored:
        message = u''

    return channel, nick, message


def _do_command(nick, args):
    global ignored

    try:
        subcmd = args.pop(0)
    except IndexError:
        subcmd = 'list'

    if subcmd == 'list':
        return u'Ignoring: {0}'.format(', '.join(ignored))

    # Only operators can add/remove
    if nick not in settings.OPERATORS:
        return u'Sorry {nick}, only operators can do that'.format(nick=nick)

    ignore_nick = args.pop(0)

    if subcmd == 'add':
        ignored.add(ignore_nick)
        return u'OK {nick}, I will ignore {ignore}'.format(nick=nick, ignore=ignore_nick)

    if subcmd == 'remove':
        ignored.discard(ignore_nick)
        return u'OK {nick}, I will stop ignoring {ignore}'.format(nick=nick, ignore=ignore_nick)


@preprocessor
@command('ignore', help=('Control the nick ignore list. '
                         'Usage: helga ignore (list|(add|remove) <nick>)'))
def ignore(client, channel, nick, message, *args):
    global ignored

    # handle
    if len(args) == 0:
        return _do_preprocess(channel, nick, message)

    return _do_command(nick, args[1])
