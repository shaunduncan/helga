import json

import smokesignal

from twisted.internet import reactor
from twisted.web import server, resource

from helga import log, settings
from helga.plugins import Plugin


logger = log.getLogger(__name__)


@smokesignal.on('signon')
def _initialize(client):
    port = getattr(settings, 'ANNOUNCEMENT_PORT', 8080)
    logger.info("Starting announcement service on port {0}".format(port))
    reactor.listenTCP(port, server.Site(AnnouncementResource(client)))


class AnnouncementResource(resource.Resource):
    isLeaf = True

    def __init__(self, client, *args, **kwargs):
        self.client = client
        resource.Resource.__init__(self, *args, **kwargs)

    def ok(self):
        return json.dumps({'status': 'OK'})

    def err(self, msg):
        return json.dumps({'status': 'ERROR', 'msg': msg})

    def render_POST(self, request):
        request.setHeader("content-type", "application/json")

        # Verify the path
        if request.path != '/announce':
            return self.err('Invalid path {0}'.format(request.path))

        # Verify the access key
        try:
            key = request.args.get('access_key', [])[0]
        except IndexError:
            return self.err('Invalid or missing access key')
        else:
            if key != settings.ANNOUNCEMENT_ACCESS_KEY:
                return self.err('Invalid or missing access key')

        # Verify the args
        try:
            channel = request.args.get('channel', [])[0]
            message = request.args.get('message', [])[0]
        except IndexError:
            return self.err('Request missing channel and/or message')
        else:
            if not all([channel, message]):
                self.err('Request missing channel and/or message')

        self.client.msg(channel, message)
        return self.ok()


class AnnouncementPlugin(Plugin):
    """
    The announcment plugin does nothing via incoming IRC messages. It's just here
    to register things.
    """
    pass
