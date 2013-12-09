from collections import defaultdict

from helga.plugins import command


@command('help', aliases=['halp'],
         help="Show the help string for any commands. Usage: helga help [<plugin>]")
def help(client, channel, nick, message, cmd, args):
    helps = defaultdict(list)
    for plugin_name in client.plugins.enabled_plugins[channel]:
        for plugin in client.plugins.plugins[plugin_name]:
            # A simple object
            if hasattr(plugin, 'help'):
                helps[plugin_name].append(plugin.help)
                continue

            # A decorated function
            elif hasattr(plugin, '_plugins'):
                fn_helps = map(lambda x: getattr(x, 'help', None), plugin._plugins)
                helps[plugin_name].extend(filter(bool, fn_helps))
                continue

    retval = []
    # Send the message to the user
    for key, value in helps.iteritems():
        retval.append(str(key))
        retval.extend(value)

    try:
        if args[0] not in helps.keys():
            return "Sorry {0}, I don't know about that plugin".format(nick)
        else:
            retval = [args[0]]
            retval.extend(helps[args[0]])
    except IndexError:
        pass

    if channel != nick:
        client.me(channel, 'whispers to {0}'.format(nick))

    retval.insert(0, "{0}, here are the plugins I know about".format(nick))
    client.msg(nick, '\n'.join(retval))

