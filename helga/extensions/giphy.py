import random

from giphypop import Giphy, GiphyApiException, GIPHY_PUBLIC_KEY

from helga import settings
from helga.extensions.base import CommandExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class GiphyExtension(CommandExtension):
    """
    A plugin for all things gifs
    """
    NAME = 'giphy'

    usage = '[BOTNICK] (gif|gifme) [<search_term> ...]'

    sad_panda = [
        "Well this is embarassing...",
        "Yeah I've got nothing %(nick)s",
        "I couldn't find anything for you %(nick)s",
        "PC LOAD LETTER",
    ]

    def __init__(self, *args, **kwargs):
        self.api_key = getattr(settings, 'GIPHY_API_KEY', GIPHY_PUBLIC_KEY)
        logger.info('Connecting to Giphy API with key %s' % self.api_key)

        self.api = Giphy(api_key=GIPHY_PUBLIC_KEY, strict=True)
        super(GiphyExtension, self).__init__(*args, **kwargs)

    def handle_message(self, opts, message):
        search = ' '.join(opts['<search_term>'])
        message.response = self.gifme(search=search)

    def gifme(self, search=None):
        """
        Hook into giphypop to find a gif. If no search term, just
        return a random gif. If a search term is given, try to translate
        it and default back to a search
        """
        try:
            return self.api.random_gif(search).media_url
        except GiphyApiException:
            try:
                return self.api.translate(search).media_url
            except GiphyApiException:
                try:
                    return self.api.search_list(search, limit=1)[0].media_url
                except (GiphyApiException, IndexError):
                    pass

        return random.choice(self.sad_panda)
