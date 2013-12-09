import random

from itertools import ifilter

import smokesignal

from helga import log
from helga.db import db
from helga.plugins import command, ACKS
from helga.plugins.core import registry


logger = log.getLogger(__name__)


@smokesignal.on('signon')
def auto_enable_plugins(*args):
    pred = lambda rec: rec['plugin'] in registry.all_plugins

    for rec in ifilter(pred, db.auto_enabled_plugins.find()):
        for channel in rec['channels']:
            logger.info("Auto-enabling plugin {0} on channel {1}".format(rec['plugin'], channel))
            registry.enable(channel, rec['plugin'])


def list_plugins(client, channel):
    enabled = set(registry.enabled_plugins[channel])
    available = registry.all_plugins - enabled

    return [
        'Plugins enabled on this channel: {0}'.format(', '.join(sorted(enabled))),
        'Available plugins: {0}'.format(', '.join(sorted(available))),
    ]


def _filter_valid(channel, *plugins):
    return filter(lambda p: p in registry.all_plugins, plugins)


def enable_plugins(client, channel, *plugins):
    plugins = _filter_valid(channel, *plugins)
    if not plugins:
        return "Sorry, but I don't know about these plugins: {0}".format(', '.join(plugins))

    registry.enable(channel, *plugins)

    for p in plugins:
        rec = db.auto_enabled_plugins.find_one({'plugin': p})
        if rec is None:
            db.auto_enabled_plugins.insert({'plugin': p, 'channels': [channel]})
        elif channel not in rec['channels']:
            rec['channels'].append(channel)
            db.auto_enabled_plugins.save(rec)

    return random.choice(ACKS)


def disable_plugins(client, channel, *plugins):
    plugins = _filter_valid(channel, *plugins)
    if not plugins:
        return "Sorry, but I don't know about these plugins: {0}".format(', '.join(plugins))

    registry.disable(channel, *plugins)

    for p in plugins:
        rec = db.auto_enabled_plugins.find_one({'plugin': p})
        if rec is None or channel not in rec['channels']:
            continue

        rec['channels'].remove(channel)
        db.auto_enabled_plugins.save(rec)

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
        return enable_plugins(client, channel, *args[1:])

    if subcmd == 'disable':
        return disable_plugins(client, channel, *args[1:])
