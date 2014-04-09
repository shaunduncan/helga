import random

from twisted.internet import reactor

from helga import log
from helga.plugins import command, postprocessor


logger = log.getLogger(__name__)


silence_acks = (
    'silence is golden',
    'shutting up',
    'biting my tongue',
    'fine, whatever',
)

unsilence_acks = (
    'speaking once again',
    'did you miss me?',
    'FINALLY',
    'thanks {nick}, i was getting bored'
)

snarks = (
    'why would you want to do that {nick}?',
    'do you really despise me that much {nick}?',
    'whatever i do what i want',
    'no can do, i love the sound of my own voice',
)

# Set of silenced channels
silenced = set()


def auto_unsilence(client, channel, length):
    global silenced

    if channel in silenced:
        silenced.discard(channel)
        client.msg(channel, "Speaking again after waiting {0} minutes".format(length//60))


@postprocessor
@command('stfu', aliases=['speak'],
         help="Tell the bot to be quiet or not. Usage: helga (speak|stfu [for <time_in_minutes>])")
def stfu(client, channel, nick, message, *args):
    global silenced

    # Handle the message postprocesor. NOTE: This won't/can't silence
    # messages that are explicitly sent via client.msg or client.me
    if len(args) == 1:
        if channel in silenced:
            logger.debug('Suppressing silenced channel %s: %s' % (channel, args[0]))
            return None

        return args[0]

    elif len(args) == 2:
        resp = ''

        if channel == nick:  # Private message
            resp = random.choice(snarks)
        elif args[0] == 'stfu':
            silenced.add(channel)
            cmdargs = args[1]
            resp = random.choice(silence_acks)

            if len(cmdargs) > 0 and cmdargs[0] == 'for':
                try:
                    length = int(cmdargs[1]) * 60
                except (TypeError, ValueError, IndexError):
                    pass
                else:
                    reactor.callLater(length, auto_unsilence, client, channel, length)
                    resp = "OK {0}, I'll be back in {1} min".format(nick, cmdargs[1])
        elif args[0] == 'speak':
            silenced.discard(channel)
            resp = random.choice(unsilence_acks)

        # Once silenced, any response will be suppressed. So we need to msg
        client.msg(channel, resp.format(nick=nick))
