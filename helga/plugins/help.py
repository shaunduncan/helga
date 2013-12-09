from collections import defaultdict

from helga.plugins import command
from helga.plugins.core import registry


@command('help', aliases=['halp'],
         help="Show the help string for any commands. Usage: helga help [<plugin>]")
def help(client, channel, nick, message, cmd, args):
    helps = defaultdict(list)
    for plugin_name in registry.enabled_plugins[channel]:
        plugin = registry.plugins[plugin_name]

        # A simple object
        if hasattr(plugin, 'help') and plugin.help:
            helps[plugin_name].append(plugin.help)

        # A decorated function
        elif hasattr(plugin, '_plugins'):
            fn_helps = filter(bool, map(lambda x: getattr(x, 'help', None), plugin._plugins))
            if fn_helps:
                helps[plugin_name].extend(fn_helps)

    retval = []
    # Send the message to the user
    for key, value in helps.iteritems():
        retval.append('[{0}] {1}'.format(str(key), '. '.join(value)))

    try:
        if args[0] not in helps.keys():
            return "Sorry {0}, I don't know about that plugin".format(nick)
        else:
            client.msg(nick, '[{0}] {1}'.format(args[0], '. '.join(helps[args[0]])))
        return
    except IndexError:
        pass

    if channel != nick:
        client.me(channel, 'whispers to {0}'.format(nick))

    retval.insert(0, "{0}, here are the plugins I know about".format(nick))
    client.msg(nick, '\n'.join(retval))

