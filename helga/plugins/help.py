from collections import defaultdict

from helga.plugins import command, registry


def format_help_string(name, *helps):
    return u'[{0}] {1}'.format(name, '. '.join(helps))


@command('help', aliases=['halp'],
         help="Show the help string for any commands. Usage: helga help [<plugin>]")
def help(client, channel, nick, message, cmd, args):
    helps = defaultdict(list)
    default_help = u'No help string for this plugin'

    for plugin_name in registry.enabled_plugins[channel]:
        try:
            plugin = registry.plugins[plugin_name]
        except KeyError:
            continue

        # A simple object
        if hasattr(plugin, 'help'):
            helps[plugin_name].append(plugin.help or default_help)

        # A decorated function
        elif hasattr(plugin, '_plugins'):
            fn_helps = filter(bool, map(lambda x: getattr(x, 'help', None), plugin._plugins))
            helps[plugin_name].extend(fn_helps or [default_help])

    try:
        plugin = args[0]
    except IndexError:
        pass
    else:
        if plugin not in registry.enabled_plugins[channel]:
            return u"Sorry {0}, I don't know about that plugin".format(nick)
        elif plugin not in helps.keys():
            return u"Sorry {0}, there's no help string for plugin '{1}'".format(nick, plugin)

        # Single plugin, it's probably ok in the public channel
        return format_help_string(plugin, *helps[plugin])

    if channel != nick:
        client.me(channel, 'whispers to {0}'.format(nick))

    retval = []
    # Send the message to the user
    for key, value in helps.iteritems():
        retval.append(format_help_string(key, *value))

    retval.insert(0, u"{0}, here are the plugins I know about".format(nick))
    client.msg(nick, u'\n'.join(retval))
