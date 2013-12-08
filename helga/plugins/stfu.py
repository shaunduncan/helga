import random

from helga.plugins import command, preprocessor


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


@preprocessor
@command('stfu', aliases=['speak'], help="Tell the bot to be quiet or not. Usage: helga (speak|stfu)")
def stfu(client, channel, nick, message, *args):
    global silenced

    # Handle the message preprocesor
    if len(args) == 0:
        if channel in silenced:
            message = ''
        return channel, nick, message

    elif len(args) == 2:
        resp = ''

        if channel == nick:  # Private message
            resp = random.choice(snarks)
        elif args[0] == 'stfu':
            silenced.add(channel)
            resp = random.choice(silence_acks)
        elif args[0] == 'speak':
            silenced.discard(channel)
            resp = random.choice(unsilence_acks)

        return resp.format(nick=nick)
