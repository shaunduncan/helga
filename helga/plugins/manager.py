import random

import smokesignal

from helga.db import db
from helga.plugins import command, ACKS


@smokesignal.on('signon')
def auto_enable_plugins(client):
    for rec in db.auto_enabled_plugins.find():
        for channel in rec['channels']:
            client.plugins.enable(channel, rec['plugin'])


def list_plugins(client, channel):
    enabled = client.plugins.enabled_plugins[channel]
    available = client.plugins.all_plugins - enabled

    return [
        'Plugins enabled on this channel: {0}'.format(', '.join(sorted(enabled))),
        'Available plugins: {0}'.format(', '.join(sorted(available))),
    ]


def enable_plugins(client, channel, *plugins):
    updated = False

    for p in plugins:
        rec = db.auto_enabled_plugins.find({'plugin': p})
        if rec is None:
            db.auto_enabled_plugins.insert({'plugin': p, 'channels': [channel]})
            updated = True
        elif channel not in rec['channels']:
            rec['channels'].append(channel)
            db.auto_enabled_plugins.save(rec)
            updated = True

    if updated:
        return random.choice(ACKS)


def disable_plugins(client, channel, *plugins):
    updated = False

    for p in plugins:
        rec = db.auto_enabled_plugins.find({'plugin': p})
        if rec is None or channel not in rec['channels']:
            continue

        rec['channels'].remove(channel)
        db.auto_enabled_plugins.save(rec)
        updated = True

    if updated:
        return random.choice(ACKS)


@command('plugins', help="Plugin management. Usage: helga plugins (list|(enable|disable) (<name> ...))")
def manager(client, channel, nick, message, cmd, args):
    """
    Manages listing plugins, or enabling and disabling them
    """
    subcmd = args[0]

    if subcmd == 'list':
        return list_plugins(client, channel)

    if subcmd == 'enable':
        return enable_plugins(client, channel, *args)

    if subcmd == 'disable':
        return disable_plugins(client, channel, *args)
