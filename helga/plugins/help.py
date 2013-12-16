from collections import defaultdict

from helga.plugins import command
from helga.plugins.core import registry


def format_help_string(name, *helps):
    return '[{0}] {1}'.format(str(name), '. '.join(helps))


@command('help', aliases=['halp'],
         help="Show the help string for any commands. Usage: helga help [<plugin>]")
def help(client, channel, nick, message, cmd, args):
    helps = defaultdict(list)
    for plugin_name in registry.enabled_plugins[channel]:
        try:
            plugin = registry.plugins[plugin_name]
        except KeyError:
            helps[plugin_name].append("Unable to load plugin '{0}'".format(plugin_name))

        # A simple object
        if hasattr(plugin, 'help') and plugin.help:
            helps[plugin_name].append(plugin.help)

        # A decorated function
        elif hasattr(plugin, '_plugins'):
            fn_helps = filter(bool, map(lambda x: getattr(x, 'help', None), plugin._plugins))
            if fn_helps:
                helps[plugin_name].extend(fn_helps)
            else:
                helps[plugin_name].append('No help string for this plugin')

    retval = []
    # Send the message to the user
    for key, value in helps.iteritems():
        retval.append(format_help_string(key, *value))

    try:
        plugin = args[0]
    except IndexError:
        pass
    else:
        if plugin not in registry.enabled_plugins[channel]:
            return "Sorry {0}, I don't know about that plugin".format(nick)
        elif plugin not in helps.keys():
            return "Sorry {0}, there's no help string for plugin '{1}'".format(nick, plugin)

        # Single plugin, it's probably ok in the public channel
        return format_help_string(plugin, *helps[plugin])

    if channel != nick:
        client.me(channel, 'whispers to {0}'.format(nick))

    retval.insert(0, "{0}, here are the plugins I know about".format(nick))
    client.msg(nick, '\n'.join(retval))
