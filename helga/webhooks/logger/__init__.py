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
        self.channel = channel
        self.date = date

    def title(self):
        return u'#{0} Channel Logs for {1}'.format(self.channel, self.date)

    def messages(self):
        logfile = '{0}.txt'.format(self.date)
        channel = '#{0}'.format(self.channel)
        logfile_full = os.path.join(settings.CHANNEL_LOGGING_DIR, channel, logfile)

        if not os.path.isfile(logfile_full):
            raise HttpError(404)

        with open(logfile_full, 'r') as fp:
            for line in fp.readlines():
                parts = line.strip().split(' - ')
                yield {
                    'time': parts.pop(0),
                    'nick': parts.pop(0),
                    'message': ' - '.join(parts),
                }


@route(r'/logger/?$')
@route(r'/logger/(?P<channel>[\w\-_]+)/?$')
@route(r'/logger/(?P<channel>[\w\-_]+)/(?P<date>[\w\-]+)/?$')
def logger(request, irc_client, channel=None, date=None):
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

    return renderer.render(page)
