import random

import smokesignal

from helga import log
from helga.db import db
from helga.plugins import command, registry, random_ack


logger = log.getLogger(__name__)

nopes = [
    u"You're not the boss of me",
    u"Whatever I do what want",
    u"You can't tell me what to do",
    u"{nick}, this incident has been reported",
    u"NO. You are now on notice {nick}"
]


@smokesignal.on('signon')
def join_autojoined_channels(client):
    if db is None:  # pragma: no cover
        logger.warning('Cannot autojoin channels. No database connection')
        return

    for channel in db.autojoin.find():
        try:
            client.join(channel['channel'])
        except:  # pragma: no cover
            logger.exception('Could not autojoin %s', channel['channel'])


def add_autojoin(channel):
    logger.info('Adding autojoin channel %s', channel)
    db_opts = {'channel': channel}

    if db.autojoin.find(db_opts).count() == 0:
        db.autojoin.insert(db_opts)
        return random_ack()
    else:
        return "I'm already doing that"


def remove_autojoin(channel):
    logger.info('Removing autojoin %s', channel)
    db.autojoin.remove({'channel': channel})
    return random_ack()


def reload_plugin(plugin):
    """
    Hooks into the registry and reloads a plugin without restarting
    """
    if registry.reload(plugin):
        return u"Successfully reloaded plugin '{0}'".format(plugin)
    else:
        return u"Failed to reload plugin '{0}'".format(plugin)


@command('operator', aliases=['oper', 'op'],
         help="Admin like control over helga. Must be an operator to use. "
              "Usage: helga (operator|oper|op) (reload <plugin>|"
              "(join|leave|autojoin (add|remove)) <channel>)")
def operator(client, channel, nick, message, cmd, args):
    """
    Admin like control over helga. Can join/leave or add/remove autojoin channels. User asking
    for this command must have his or her nick listed in OPERATORS list in helga settings.
    """
    if nick not in client.operators:
        return random.choice(nopes).format(nick=nick)

    subcmd = args[0]

    if subcmd in ('join', 'leave'):
        channel = args[1]
        if channel.startswith('#'):
            getattr(client, subcmd)(channel)

    elif subcmd == 'autojoin':
        op, channel = args[1], args[2]
        if op == 'add':
            return add_autojoin(channel)
        elif op == 'remove':
            return remove_autojoin(channel)

    elif subcmd == 'nsa':
        # Never document this
        return client.msg(args[1], ' '.join(args[2:]))

    # Reload a plugin without restarting
    elif subcmd == 'reload':
        return reload_plugin(args[1])
