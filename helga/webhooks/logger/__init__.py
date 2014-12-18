import os

import pystache

from helga import settings
from helga.plugins.webhooks import HttpError, route


class Index(object):
    """
    Rendered object for the logger index page meant to show the full list
    of logged channels.
    """

    def title(self):
        return u'Channel Logs'

    def channels(self):
        log_dir = settings.CHANNEL_LOGGING_DIR

        if not os.path.isdir(log_dir):
            raise StopIteration

        for chan in sorted(os.listdir(log_dir)):
            yield chan.lstrip('#')


class ChannelIndex(object):
    """
    Rendered object for the logger channel index page meant to show the full list
    of log files (UTC dates) for a given IRC channel.
    """

    def __init__(self, channel):
        self.channel = channel

    def title(self):
        return u'#{0} Channel Logs'.format(self.channel)

    def dates(self):
        channel = '#{0}'.format(self.channel)
        basedir = os.path.join(settings.CHANNEL_LOGGING_DIR, channel)

        if not os.path.isdir(basedir):
            raise HttpError(404)

        for date in sorted(os.listdir(basedir), reverse=True):
            yield date.replace('.txt', '')


class ChannelLog(object):
    """
    Rendered object for displaying the full contents of a channel log for a
    given channel and date.
    """

    def __init__(self, channel, date):
        self.channel_name = channel
        self.date = date
        self.logfile = '{0}.txt'.format(self.date)
        self.channel = '#{0}'.format(self.channel_name)

    @property
    def logfile_path(self):
        return os.path.join(settings.CHANNEL_LOGGING_DIR, self.channel, self.logfile)

    def title(self):
        """
        The page title
        """
        return u'{0} Channel Logs for {1}'.format(self.channel, self.date)

    def messages(self):
        """
        Generator for logged channel messages as a dictionary
        of the message time, message nick, and message contents
        """
        if not os.path.isfile(self.logfile_path):
            raise HttpError(404)

        with open(self.logfile_path, 'r') as fp:
            for line in fp.readlines():
                parts = line.strip().split(' - ')
                yield {
                    'time': parts.pop(0),
                    'nick': parts.pop(0),
                    'message': ' - '.join(parts),
                }

    def download(self, request):
        """
        Offers this logfile as a download
        """
        request.setHeader('Content-Type', 'text/plain')
        request.setHeader('Content-Disposition',
                          'attachment; filename={0}'.format(self.logfile))
        with open(self.logfile_path, 'r') as fp:
            return '\n'.join(line.strip() for line in fp.readlines())


@route(r'/logger/?$')
@route(r'/logger/(?P<channel>[\w\-_]+)/?$')
@route(r'/logger/(?P<channel>[\w\-_]+)/(?P<date>[\w\-]+)(?P<as_text>\.txt)?/?$')
def logger(request, irc_client, channel=None, date=None, as_text=None):
    if not settings.CHANNEL_LOGGING:
        raise HttpError(501, 'Channel logging is not enabled')

    request.setHeader('Content-Type', 'text/html')
    renderer = pystache.renderer.Renderer(
        search_dirs=os.path.dirname(os.path.abspath(__file__))
    )

    if channel is None:
        page = Index()
    elif date is None:
        page = ChannelIndex(channel)
    else:
        page = ChannelLog(channel, date)
        if as_text is not None:
            return page.download(request)

    return renderer.render(page)
