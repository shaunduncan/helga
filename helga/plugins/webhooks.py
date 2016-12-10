"""
Webhook HTTP server plugin and core webhook API

Webhooks provide a way to expose HTTP endpoints that can interact with helga. A command
plugin manages an HTTP server that is run on a port specified by setting
:data:`helga.settings.WEBHOOKS_PORT` (default 8080). An additional, optional setting that can be
used for routes requiring HTTP basic auth is :data:`helga.settings.WEBHOOKS_CREDENTIALS`,
which should be a list of tuples, where each tuple is a pair of (username, password).

Routes are URL path endpoints. On the surface they are just python callables decorated using
:func:`@route <route>`. The route decorated must be given a path regex, and optional list of
HTTP methods to accept. Webhook plugins must be registered in the same way normal plugins are
registered, using setuptools entry_points. However, they must belong to the entry_point group
``helga_webhooks``. For example::

    setup(entry_points={
        'helga_webhooks': [
            'api = myapi.decorated_route'
        ]
    })

For more information, see :ref:`webhooks`
"""
import functools
import pkg_resources
import re

from twisted.internet import reactor
from twisted.web import server, resource
from twisted.web.error import Error

import smokesignal

from helga import log, settings
from helga.plugins import Command, registry
from helga.util.encodings import from_unicode


logger = log.getLogger(__name__)


# Subclassed only for better naming
class HttpError(Error):
    __doc__ = Error.__doc__


class WebhookPlugin(Command):
    """
    A command plugin that manages running an HTTP server for webhook routes and services. Usage::

        helga webhooks (start|stop|routes)

    Both ``start`` and ``stop`` are privileged actions and can start and stop the HTTP listener for
    webhooks respectively. To use them, a user must be configured as an operator. The ``routes``
    subcommand will list all of the URL routes known to the webhook listener.

    Webhook routes are generally loaded automatically if they are installed. There are whitelist
    and blacklist controls to limit loading webhook routes (see :data:`~helga.settings.ENABLED_WEBHOOKS`
    and :data:`~helga.settings.DISABLED_WEBHOOKS`)
    """
    command = 'webhooks'
    help = ('HTTP service for interacting with helga. Command options usage: '
            'helga webhooks (start|stop|routes). Note: start/stop'
            'can be run only by helga operators')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        # Per issue 137, these were previously set on signon, but there is a bit of a
        # chicken and egg situation where routes in the same module as commands and matches
        # would try to register themselves before the connection was made, so the command
        # or match would fail to load.
        self.root = WebhookRoot()
        self.site = server.Site(self.root)
        self.port = getattr(settings, 'WEBHOOKS_PORT', 8080)

        self.webhook_names = set(ep.name for ep in pkg_resources.iter_entry_points('helga_webhooks'))

        self.whitelist_webhooks = self._create_webhook_list('ENABLED_WEBHOOKS', default=True)
        self.blacklist_webhooks = self._create_webhook_list('DISABLED_WEBHOOKS', default=True)

        @smokesignal.on('signon')
        def setup(client):  # pragma: no cover
            self._start(client)
            self._init_routes()

    def _create_webhook_list(self, setting_name, default):
        """
        Used to get either webhook whitelists or blacklists

        :param setting_name: either ENABLED_WEBHOOKS or DISABLED_WEBHOOKS
        :param default: the default value to use if the setting does not exist
        """
        webhooks = getattr(settings, setting_name, default)
        if isinstance(webhooks, bool):
            return self.webhook_names if webhooks else set()
        else:
            return set(webhooks or [])

    def _init_routes(self):
        """
        Initialize all webhook routes by loading entry points while honoring both
        webhook whitelist and blacklist
        """
        if not self.whitelist_webhooks:
            logger.debug('Webhook whitelist was empty, none, or false. Skipping')
            return

        for entry_point in pkg_resources.iter_entry_points(group='helga_webhooks'):
            if entry_point.name in self.blacklist_webhooks:
                logger.info('Skipping blacklisted webhook %s', entry_point.name)
                continue

            if entry_point.name not in self.whitelist_webhooks:
                logger.info('Skipping non-whitelisted webhook %s', entry_point.name)
                continue

            try:
                logger.info('Loading webhook %s', entry_point.name)
                entry_point.load()
            except:
                logger.exception('Error loading webhook %s', entry_point)

    def _start(self, client=None):
        logger.info('Starting webhooks service on port %s', self.port)
        self.root.chat_client = client
        self.tcp = reactor.listenTCP(self.port, self.site)

    def _stop(self):
        logger.info('Stopping webhooks service on port %s', self.port)
        self.tcp.stopListening()
        self.tcp.loseConnection()
        self.tcp = None

    def add_route(self, fn, path, methods):
        """
        Adds a route handler function to the root web resource at a given path
        and for the given methods

        :param fn: the route handler function
        :param path: the URL path of the route
        :param methods: list of HTTP methods that the route should respond to
        """
        self.root.add_route(fn, path, methods)  # pragma: no cover

    def list_routes(self, client, nick):
        """
        Messages a user with all webhook routes and their supported HTTP methods

        :param client: an instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        :param nick: the nick of the chat user to message
        """
        client.msg(nick, u'{0}, here are the routes I know about'.format(nick))
        for pattern, route in self.root.routes.iteritems():
            http_methods = route[0]  # Route is a tuple (http_methods, function)
            client.msg(nick, u'[{0}] {1}'.format(','.join(http_methods), pattern))

    def control(self, action):
        """
        Control the running HTTP server. Intended for helga operators.

        :param action: the action to perform, either 'start' or 'stop'
        """
        running = self.tcp is not None

        if action == 'stop':
            if running:
                self._stop()
                return u"Webhooks service stopped"
            return u"Webhooks service not running"

        if action == 'start':
            if not running:
                self._start()
                return u"Webhooks service started"
            return u"Webhooks service already running"

    def run(self, client, channel, nick, msg, cmd, args):
        try:
            subcmd = args[0]
        except IndexError:
            subcmd = 'routes'

        if subcmd == 'routes':
            client.me(channel, u'whispers to {0}'.format(nick))
            self.list_routes(client, nick)
        elif subcmd in ('start', 'stop'):
            if nick not in client.operators:
                return u"Sorry {0}, Only an operator can do that".format(nick)
            return self.control(subcmd)


class WebhookRoot(resource.Resource):
    """
    The root HTTP resource the webhook HTTP server uses to respond to requests. This
    manages all registered webhook route handlers, manages running them, and manages
    returning any responses generated.
    """
    isLeaf = True

    def __init__(self, *args, **kwargs):
        #: An instance of :class:`helga.comm.irc.Client` or :class:`helga.comm.xmpp.Client`
        self.chat_client = None

        #: A dictionary of regular expression URL paths as keys, and two-tuple values
        #: of allowed methods, and the route handler function
        self.routes = {}

    def add_route(self, fn, path, methods):
        """
        Adds a route handler function to the root web resource at a given path
        and for the given methods

        :param fn: the route handler function
        :param path: the URL path of the route
        :param methods: list of HTTP methods that the route should respond to
        """
        self.routes[path] = (methods, fn)

    def render(self, request):
        """
        Renders a response for an incoming request. Handles finding and dispatching the route
        matching the incoming request path. Any response string generated will be explicitly
        encoded as a UTF-8 byte string.

        If no route patch matches the incoming request, a 404 is returned.

        If a route is found, but the request uses a method that the route handler does not
        support, a 405 is returned.

        :param request: The incoming HTTP request, ``twisted.web.http.Request``
        :returns: a string with the HTTP response content
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

        # Handle raised HttpErrors
        try:
            # Explicitly return a byte string. Twisted expects this
            return from_unicode(fn(request, self.chat_client, **match.groupdict()))
        except HttpError as e:
            request.setResponseCode(int(e.status))
            return e.message or e.response


def authenticated(fn):
    """
    Decorator for declaring a webhook route as requiring HTTP basic authentication.
    Incoming requests validate a supplied basic auth username and password against the list
    configured in the setting :data:`~helga.settings.WEBHOOKS_CREDENTIALS`. If no valid
    credentials are supplied, an HTTP 401 response is returned.

    :param fn: the route handler to decorate
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
    Decorator to register a webhook route. This requires a path regular expression, and
    optionally a list of HTTP methods to accept, which defaults to accepting ``GET`` requests
    only. Incoming HTTP requests that use a non-allowed method will receive a 405 HTTP response.

    :param path: a regular expression string for the URL path of the route
    :param methods: a list of accepted HTTP methods for this route, defaulting to ``['GET']``

    Decorated routes must follow this pattern:

    .. function:: func(request, client)
        :noindex:

        :param request: The incoming HTTP request, ``twisted.web.http.Request``
        :param client: The client connection. An instance of :class:`helga.comm.irc.Client`
                       or :class:`helga.comm.xmpp.Client`
        :returns: a string HTTP response
    """
    plugin = registry.get_plugin('webhooks')
    if methods is None:
        methods = ['GET']

    def wrapper(fn):
        if plugin is not None:
            plugin.add_route(fn, path, methods)
        return fn

    return wrapper
