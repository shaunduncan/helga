.. _webhooks:

Webhooks
========
As of helga version 1.3, helga includes support for pluggable webhooks that can interact
with the running bot or communicate via IRC. The webhook architecture is extensible much
in the way that plugins work, allowing you to create new or custom HTTP services.


.. _webhooks.overview:

Overview
--------
The webhooks system has two important aspects and core concepts: the HTTP server and routes.


.. _webhooks.overview.server:

HTTP Server
^^^^^^^^^^^
The webhooks system consists of an HTTP server that is managed by a command plugin named
:ref:`webooks <builtin.plugins.webhooks>`. This plugin is enabled by default and handles starting the
HTTP server is started when helga successfully signs on to IRC. The server process is configured to
listen on a port specified by the setting :data:`~helga.settings.WEBHOOKS_PORT`.

The actual implementation of this HTTP server is a combination of a TCP listner using the Twisted
reactor, and ``twisted.web.server.Site`` with a single root resource (see
:class:`~helga.plugins.webhooks.WebhookRoot`) that manages each registered URL route.

.. note::

    This server is managed via a plugin only so it can be controlled via IRC.


.. _webhooks.overview.routes:

Routes
^^^^^^
Routes are the plugins of the webhook system. They are essentially registered URL paths that have
some programmed behavior. For example, ``http://localhost:8080/github``, or ``/github`` specifically,
might be the registered route for a webhook that announces github code pushes on an IRC channel.
Routes are declared using a decorator (see :ref:`webhooks.creating`), which will feel familiar
to anyone with `flask`_ experience. At this time, routes also support HTTP basic authentication,
which is configurable with a setting :data:`~helga.settings.WEBHOOKS_CREDENTIALS`.


.. _webhooks.creating:

The ``@route`` Decorator
------------------------
Much like the plugin system, webhook routes are created using an easy to use decorator API. At
the core of this API is a single decorator :func:`@route <helga.plugins.webhooks.route>`, which
will feel familiar to anyone with `flask`_ experience:

.. autofunction:: helga.plugins.webhooks.route
    :noindex:

For example::

    from helga.plugins.webhooks import route

    @route(r'/foo')
    def foo(request, client):
        client.msg('#foo', 'someone hit the /foo endpoint')
        return 'message sent'

Routes can be configured to also support URL parameters, which act similarly to `django`_'s URL
routing mechanisms. By introducing named pattern groups in the regular expression string. These
will be passed as keyword arguments to the decorated route handler::

    from helga.plugins.webhooks import route

    @route(r'/foo/(?P<bar>[0-9]+)')
    def foo(request, client, bar):
        client.msg('#foo', 'someone hit the /foo endpoint with bar {0}'.format(bar))
        return 'message sent'


.. _webhooks.authentication:

Authenticated Routes
--------------------
The webhooks system includes mechanisms for restricting routes to authenticated users. Note,
that this is only supported to handle HTTP basic authentication. Auth credentials are currently
limited to hard-coded username and password pairs configured as a list of two-tuples, the setting
:data:`~helga.settings.WEBHOOKS_CREDENTIALS`. Routes are declared as requiring authentication
using the :func:`@authenticated <helga.plugins.webhooks.authenticated>` decorator:

.. autofunction: helga.plugins.webhooks.authenticated
    :noindex:

For example::

    from helga.plugins.webhooks import authenticated, route

    @route(r'/foo')
    @authenticated
    def foo(request, client):
        client.msg('#foo', 'someone hit the /foo endpoint')
        return 'message sent'

.. important::

    The :func:`@authenticated <helga.plugins.webhooks.authenticated>` decorator **must** be the
    first decorator used for a route handler, otherwise the authentication check will not happen
    prior to a route being handled. This requirement may change in the future.


.. _webhooks.http_status:

Sending Non-200 Responses
-------------------------
By default, route handlers will send a 200 response to any incoming request. However, in some
cases it may be necessary to explicitly return a non-200 response. In order to accomplish this,
a route handler can manually set the response status code on the request object::

    from helga.plugins.webhooks import route

    @route(r'/foo')
    def foo(request, client):
        request.setResponseCode(404)
        return 'foo is always 404'

In addition to this, route handlers can also raise :exc:`helga.plugins.webhooks.HttpError`::

    from helga.plugins.webhooks import route, HttpError

    @route(r'/foo')
    def foo(request, client):
        raise HttpError(404, 'foo is always 404')


.. _webhooks.templates:

Using Templates
---------------
When installed, helga will have `pystache`_ installed as well, which can be used for templating
webhooks that produce HTML responses. It is important though that any webhooks be packaged so that
any external ``.mustache`` templates are packaged as well, which can be done by adding to a
``MANIFEST.in`` file (see :ref:`webhooks.packaging`)::

    recursive-include . *.mustache


.. _webhooks.unicode:

Handling Unicode
----------------
Handling unicode for webhooks is not as strict as with plugins, but the same guidelines should follow.
For example, webhooks should return unicode, but know that unicode strings are explicitly encoded as
UTF-8 byte strings. See the plugin documentation :ref:`plugins.unicode`.


.. _webhooks.database:

Accessing The Database
----------------------
Database access for webhooks follows the same rules as for plugins. See the plugin documentation
:ref:`plugins.database`


.. _webhooks.settings:

Requiring Settings
------------------
Requiring settings for webhooks follows the same rules as for plugins. See the plugin documentation
:ref:`plugins.settings`


.. _webhooks.packaging:

Packaging and Distribution
--------------------------
Much like plugins, webhooks are also installable python modules. For that reason, the rules for
packaging and distributing webhooks are the same as with plugins (see plugin :ref:`plugins.packaging`).
However, there is one minor difference with respect to declaring the webhook entry point. Rather
than indicating the webhook as a ``helga_plugins`` entry point, it should be placed in an entry
point section named ``helga_webhooks``. For example::

    setup(
        entry_points=dict(
            helga_webhooks=[
                'api = myapi:decorated_route'
            ]
        )
    )


.. _webhooks.installing:

Installing Webhooks
-------------------
Webhooks are installed in the same manner that plugins are installed (see plugin :ref:`plugins.installing`).
And much like plugins, there are settings to control both a whitelist and blacklist for loading webhook
routes (see :data:`~helga.settings.ENABLED_PLUGINS` and :data:`~helga.settings.DISABLED_PLUGINS`). To
explicitly whitelist webhook routes to be loaded, use :data:`~helga.settings.ENABLED_WEBHOOKS`. To
explicitly blacklist webhook routes from being loaded, use :data:`~helga.settings.DISABLED_WEBHOOKS`.


.. _`flask`: http://flask.pocoo.org/
.. _`django`: https://www.djangoproject.com/
.. _`pystache`: https://github.com/defunkt/pystache
