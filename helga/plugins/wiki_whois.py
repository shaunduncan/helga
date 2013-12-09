from helga import settings
from helga.plugins import command


@command('showme', aliases=['whois', 'whothehellis'],
         help="Show a URL for the user's intranet page. Usage: helga (showme|whois|whothehellis) <nick>")
def wiki_whois(client, channel, nick, message, cmd, args):
    """
    Show the intranet page for a user. Settings must have a WIKI_URL value with formattable
    substring named {user}
    """
    return settings.WIKI_URL.format(user=args[0])
