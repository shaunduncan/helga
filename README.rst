helga
=====

.. image:: https://github.com/shaunduncan/helga/workflows/CI/badge.svg
    :target: https://github.com/shaunduncan/helga/actions

.. image:: https://codecov.io/gh/shaunduncan/helga/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/shaunduncan/helga

.. image:: https://img.shields.io/pypi/v/helga.svg
    :target: https://pypi.python.org/pypi/helga

.. image:: https://img.shields.io/pypi/pyversions/helga.svg
    :target: https://pypi.python.org/pypi/helga

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


About
-----
Helga is a full-featured chat bot for Python 3.8+ using `Twisted`_. Helga originally started
as a python fork of a perl-based IRC bot `olga`_, but has grown considerably since then. Early
versions limited support to IRC, but now include other services like XMPP, HipChat, Slack, and Discord.
Full documentation can be found at http://helga.readthedocs.org.

**Note:** Version 2.0.0+ requires Python 3.8 or higher. For Python 2.7 support, use version 1.x.


Supported Backends
------------------

Helga supports IRC, XMPP, HipChat, Slack, and Discord out of the box. Note, however, that
helga originally started as an IRC bot, so much of the terminology will reflect that. The current
status of non-IRC support varies by backend. In the future, helga may have a much more robust and
pluggable backend system to allow connections to any number of chat services.


Contributing
------------
Contributions are **always** welcomed, whether they be in the form of bug fixes, enhancements,
or just bug reports. To report any issues, please create a ticket on `github`_. For code
changes, please note that any pull request will be denied a merge if the test suite fails.

See `CONTRIBUTING.md`_ for detailed contribution guidelines, including:

- Development setup with modern tools (Black, Ruff, Mypy)
- Pre-commit hooks for code quality
- Testing guidelines
- Code style standards
- Pull request process

If you are looking to get help with helga, join the #helgabot IRC channel on freenode.


Docker
------

A docker compose file is included, which has a irc server and mongodb instance. Once you bring
the cluster using `docker-compose up`, you can connect to the irc on localhost port 6667, and
join the #test channel.


Deployment
----------

IBM Cloud
~~~~~~~~~

Helga can be easily deployed to IBM Cloud using Cloud Foundry. A complete deployment guide,
configuration files, and automated deployment script are included:

- **Quick Start**: Run ``./deploy-ibmcloud.sh`` for an interactive deployment
- **Manual Deployment**: See ``IBM_CLOUD_DEPLOYMENT.md`` for detailed instructions
- **Configuration**: Edit ``ibmcloud_settings.py`` or use environment variables

The deployment includes:

- Cloud Foundry manifest (``manifest.yml``)
- IBM Cloud-specific settings (``ibmcloud_settings.py``)
- MongoDB service integration
- Environment-based configuration

For complete instructions, see `IBM_CLOUD_DEPLOYMENT.md`_.

Docker
~~~~~~

A docker compose file is included for local development and testing. It includes an IRC server
and MongoDB instance. Once you bring up the cluster using ``docker-compose up``, you can connect
to the IRC server on localhost port 6667 and join the #test channel.


License
-------
Copyright (c) 2014 Shaun Duncan

Helga is open source software, dual licensed under the `MIT`_ and `GPL`_ licenses. Dual licensing
was chosen for this project so that plugin authors can create plugins under their choice
of license that is compatible with this project.

Modernization
-------------

Helga has been modernized with current Python best practices and tooling. See `MODERNIZATION.md`_
for details on:

- Modern Python packaging (pyproject.toml)
- GitHub Actions CI/CD
- Pre-commit hooks and linting (Ruff, Black, Mypy)
- Enhanced Docker configuration
- Automated dependency updates

.. _`GPL`: https://github.com/shaunduncan/helga/blob/master/LICENSE-GPL
.. _`MIT`: https://github.com/shaunduncan/helga/blob/master/LICENSE-MIT
.. _`Twisted`: https://twistedmatrix.com/trac/
.. _`olga`: https://github.com/thepeopleseason/olga
.. _`github`: https://github.com/shaunduncan/helga/issues
.. _`IBM_CLOUD_DEPLOYMENT.md`: IBM_CLOUD_DEPLOYMENT.md
.. _`CONTRIBUTING.md`: CONTRIBUTING.md
.. _`MODERNIZATION.md`: MODERNIZATION.md
