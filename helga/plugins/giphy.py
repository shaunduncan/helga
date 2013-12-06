import random

from giphypop import Giphy, GiphyApiException, GIPHY_PUBLIC_KEY

from helga import log, settings
from helga.plugins import command


logger = log.getLogger(__name__)

# Snarky responses on failure
responses = [
    "Well this is embarassing...",
    "Yeah I've got nothing {nick}",
    "I couldn't find anything for you {nick}",
    "PC LOAD LETTER",
]


@command('gif', aliases=['gifme'], help='Search giphy for an animated gif. Usage: helga gif <search term>')
def giphy(client, channel, nick, message, cmd, args):
    key = getattr(settings, 'GIPHY_API_KEY', GIPHY_PUBLIC_KEY)
    api = Giphy(api_key=key, strict=True)

    search = ' '.join(args)

    try:
        return api.random_gif(search).media_url
    except GiphyApiException:
        try:
            return api.translate(search).media_url
        except GiphyApiException:
            try:
                return api.search_list(search, limit=1)[0].media_url
            except (GiphyApiException, IndexError):
                pass

    return random.choice(responses).format(nick=nick)
