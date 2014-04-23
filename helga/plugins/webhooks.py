import functools
import pkg_resources
import re

from twisted.internet import reactor
from twisted.web import server, resource

import smokesignal

from helga import log, settings
from helga.plugins import Command, registry


logger = log.getLogger(__name__)


class WebhookPlugin(Command):
    """
    Webhooks provides a way to expose HTTP endpoints that can interact with
    helga. An HTTP listener will be started on a port specified by setting
    WEBHOOKS_PORT (default 8080). An additional, optional setting that can
    be used for routes requiring HTTP basic auth is WEBOOKS_CREDENTIALS, which
    should be a list of tuples, where each tuple is a pair of (username, password).

    Routes are HTTP path endpoints. On the surface they are just python
    callables decorated using @route. The route decorate (described below)
    must be given a path regex, and optional HTTP methods to accept. Webhook
    plugins must be registered in the same way normal plugins are registered,
    using setuptools entry_points. However, they must belong to the entry_point
    group ``helga_webhooks``. For example::

        setup(entry_points={
            'helga_webhooks': [
                'api = myapi.decorated_route'
            ]
        })

    This will make new webhooks installable in a very simple, and repeatable way.

    The exposed webhook plugin gives control for starting and stopping the HTTP
    service, as well as listing available routes.
    """
    command = 'webhooks'
    help = ('HTTP service for interacting with helga. Command options usage: '
            'helga webhooks (start|stop|routes). Note: start/stop'
            'can be run only by helga operators')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.root = None
        self.site = None
        self.port = getattr(settings, 'WEBHOOKS_PORT', 8080)

        @smokesignal.on('signon')
        def setup(client):
            self._start(client)
            self._init_routes()

    def _init_routes(self):
        for entry_point in pkg_resources.iter_entry_points(group='helga_webhooks'):
            try:
                logger.debug('Loading webhook {0}'.format(entry_point.name))
                entry_point.load()
            except:
                logger.exception("Error loading webhook {0}".format(entry_point))

    def _start(self, client=None):
        logger.info("Starting webhooks service on port {}".format(self.port))

        if self.root is None:
            self.root = WebhookRoot(client)
        else:
            self.root.irc_client = client

        if self.site is None:
            self.site = server.Site(self.root)

        self.tcp = reactor.listenTCP(self.port, self.site)

    def _stop(self):
        logger.info("Stopping webhooks service on port {}".format(self.port))
        self.tcp.stopListening()
        self.tcp.loseConnection()
        self.tcp = None

    def add_route(self, fn, path, methods):
        """
        Adds a route to the root web resource
        """
        self.root.add_route(fn, path, methods)

    def list_routes(self, client, nick):
        """
        Messages a user with all webhook routes and their supported HTTP methods
        """
        client.msg(nick, '{}, here are the routes I know about'.format(nick))
        for pat, route in self.root.routes.iteritems():
            client.msg(nick, '[{}] {}'.format(','.join(route[0]), pat))

    def control(self, action):
        """
        Operator-level control over stop/start of the running TCP listener
        """
        running = self.tcp is not None

        if action == 'stop':
            if running:
                self._stop()
                return "Webhooks service stopped"
            return "Webhooks service not running"

        if action == 'start':
            if not running:
                self._start()
                return "Webhooks service started"
            return "Webhooks service already running"

    def run(self, client, channel, nick, msg, cmd, args):
        try:
            subcmd = args[0]
        except IndexError:
            subcmd = 'routes'

        if subcmd == 'routes':
            client.me(channel, 'whispers to {}'.format(nick))
            self.list_routes(client, nick)
        elif subcmd in ('start', 'stop'):
            if nick not in client.operators:
                return "Sorry {}, Only an operator can do that".format(nick)
            return self.control(subcmd)


class WebhookRoot(resource.Resource):
    isLeaf = True

    def __init__(self, irc_client, *args, **kwargs):
        self.irc_client = irc_client

        # Routes is a dict of regex path -> (allowed_methods, callable)
        self.routes = {}

    def add_route(self, fn, path, methods):
        """
        Adds a webhook route for service
        """
        self.routes[path] = (methods, fn)

    def render(self, request):
        """
        Handle finding and dispatching the route matching the incoming request path
        """
        request.setHeader('Server', 'helga')
        for pat, route in self.routes.iteritems():
            match = re.match(pat, request.path)
            if match:
                break
        else:
            request.setResponseCode(404)
            return '404 Not Found'

        # Ensure that this route handles the request method
        methods, fn = route
        if request.method.upper() not in methods:
            request.setResponseCode(405)
            return '405 Method Not Allowed'

        return fn(request, self.irc_client, **match.groupdict())


def authenticated(fn):
    """
    A wrapper for a webhook route that ensures value HTTP basic auth
    credentials are supplied. Example::

        @authenticated
        @route('/foo/bar')
        def my_endpoint(request, irc_client):
            pass

    Any valid credentials in the setting WEBHOOKS_CREDENTIALS, which should
    be a list of tuples (username, password) will be allowed. If no valid
    credentials are supplied, an HTTP 401 is returned
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


def route(path, methods=None):
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
    plugin = registry.get_plugin('webhooks')
    if methods is None:
        methods = ['GET']

    def wrapper(fn):
        plugin.add_route(fn, path, methods)
        return fn

    return wrapper
