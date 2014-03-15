import functools
import re
import smokesignal

from twisted.internet import reactor
from twisted.web import server, resource

from helga import log, settings


logger = log.getLogger(__name__)


@smokesignal.on('signon')
def init_webhooks(irc_client):
    port = getattr(settings, 'WEBHOOKS_PORT', 8080)
    logger.info("Starting webhooks service on port {}".format(port))
    reactor.listenTCP(port, server.Site(WebhooksRoot(irc_client)))


class WebhooksRoot(resource.Resource):
    isLeaf = False

    def __init__(self, irc_client, *args, **kwargs):
        self.irc_client = irc_client

        # Routes is a dict of regex path -> (allowed_methods, callable)
        self.routes = {}

    def authenticate(self, request):
        user = request.getUser()
        password = request.getPassword()

        return user == settings.WEBHOOKS_USER and password == settings.WEBHOOKS_PASSWORD

    def render(self, request):
        """
        Handle finding and dispatching the route matching the incoming request path
        """
        for pat, route in self.routes.iteritems():
            match = re.match(pat, request.path)
            if match:
                break
        else:
            raise SystemExit

        # Ensure that this route handles the request method
        methods, fn = route
        if request.method.upper() not in methods:
            request.setResponseCode(405)
            return '405 Method Not Allowed'

        return fn(request, self.irc_client, **match.groupdict())


def basic_auth(fn):
    """
    A wrapper for a webhook route that ensures value HTTP basic auth
    credentials are supplied
    """
    @functools.wraps(fn)
    def ensure_authenticated(request, *args, **kwargs):
        for user, password in getattr(settings, 'WEBHOOKS_CREDENTIALS', []):
            if user == request.getUser() and password == request.getPassword():
                return fn(request, *args, **kwargs)

        # No valid basic auth provided
        request.setResponseCode(401)
        return '401 Unauthorized'
    return ensure_authenticated


def route(regex, methods=None):
    """
    Decorator to register a webhook route. You must specify a path
    regular expression, and optionally a list of HTTP methods to accept.
    If you do not specify a list of HTTP methods, only GET requests will
    be served. All regex matches must be named groups and they will be passed
    as keyword arguments. For those who are familiar with something
    like Flask, this will feel very similar. Example::

        @route(r'/users/(?P<user_id>[0-9]+)')
        def get_user(request, irc_client, user_id):
            pass

        @route(r'/foo/(?P<subpage>[a-z]+)/(?P<page_id>[0-9]+)', methods=['GET', 'POST'])
        def page(request, irc_client, subpage, page_id):
            pass

    Note that route callables (shown above) must accept as the first two
    positional arguments a request object, and the current irc client.
    """
    pass
