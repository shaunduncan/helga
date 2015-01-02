.. currentmodule:: helga.settings

.. _config:

Configuring Helga
=================
As mentioned in :ref:`getting_started`, when you install helga, a ``helga`` console script is
created that will run the bot process. This is the simplest way to run helga, however, it will
assume various default settings like assuming that both the IRC and MongoDB servers to which you
wish to connect run on your local machine. This may not be ideal for running helga in a production
environment. For this reason you may wish to create your own configuration for helga.


.. _config.custom:

Custom Settings
---------------
Helga settings files are essentially executable python files. If you have ever worked with django
settings files, helga settings will feel very similar. Helga does assume some configuration defaults,
but you can (and should) use a custom settings file. The behavior of any custom settings file you use
is to overwrite any default configuration helga uses. For this reason, you do not need to apply
all of the configuration settings (listed below) known. For example, a simple settings file might only be::

    SERVER = {
        'HOST': 'www.example.com',
        'PORT': 8080,
    }

There are two ways in which you can use a custom settings file. First, you could export a ``HELGA_SETTINGS``
environment variable. Alternatively, you can indicate this via a ``--settings`` argument to the ``helga``
console script. For example:

.. code-block:: bash

    $ export HELGA_SETTINGS=foo.settings
    $ helga

Or:

.. code-block:: bash

    $ helga --settings=/etc/helga/settings.py

In either case, this value should be an absolute filesystem path to a python file like ``/path/to/foo.py``,
or a python module string available on ``$PYTHONPATH`` like ``path.to.foo``.


.. _config.default:

Default Configuration
---------------------
Running the ``helga`` console script with no arguments will run helga using a default configuration.
For a full list of the included default settings, see :mod:`helga.settings`. 


.. _config.default.plugins:

Builtin Plugin Settings
^^^^^^^^^^^^^^^^^^^^^^^

Some builtin helga plugins utilize settings for configuration, as listed below.


.. _config.default.plugins.facts:

Facts Plugin
""""""""""""
See :ref:`builtin.plugins.facts`

``FACTS_REQUIRE_NICKNAME``
    A boolean, if True, would require the bot's nick to show a stored fact. For example, if True,
    'foo?' could only be shown with 'helga foo?'. (default: False)


.. _config.default.plugins.giphy:

Giphy Plugin
""""""""""""

See :ref:`builtin.plugins.giphy`

``GIPHY_API_KEY``
    Access key for the `giphy`_ API endpoint. Default is giphy's public API key.


.. _config.default.plugins.jira:

JIRA Plugin
"""""""""""

See :ref:`builtin.plugins.jira`

``JIRA_URL``
    A URL format string for showing JIRA links. This should contain a format parameter '{ticket}'.
    (default: 'http://localhost/{ticket}')

``JIRA_REST_API``
    A URL string, if non-empty, for a JIRA REST API for the JIRA plugin to use. Much like ``JIRA_URL``,
    this should contain a format parameter '{ticket}'. Note that this requires a minmum JIRA version to
    work, one that has the updated REST api. See
    https://docs.atlassian.com/software/jira/docs/api/REST/latest/. (default: 'http://localhost/api/{ticket}')

``JIRA_SHOW_FULL_DESCRIPTION``
    A boolean, if False, only the formatted ``JIRA_URL`` will be returned for JIRA links.
    If True, a full ticket title will be shown. This requires ``JIRA_REST_API`` to be set.
    (default: False)

``JIRA_AUTH``
    A two-tuple of JIRA credentials, username and password. If empty, no authentication is used.
    (default: ('', ''))


.. _config.default.plugins.reviewboard:

Reviewboard Plugin
""""""""""""""""""

See :ref:`builtin.plugins.reviewboard`

``REVIEWBOARD_URL``
    A URL string format for showing ReviewBoard links. This should contain a format parameter
    '{review}'. (default: 'http://localhost/{review}')


.. _config.default.plugins.wiki_whois:

Wiki WHOIS Plugin
"""""""""""""""""

See :ref:`builtin.plugins.wiki_whois`

``WIKI_URL``
    A URL string format for showing user pages on a wiki, such as example.com/^user. This should
    contian a format parameter '{user}'. (default: 'http://localhost/{user}')


.. _`giphy`: http://giphy.com/
