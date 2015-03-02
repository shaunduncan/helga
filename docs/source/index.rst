.. helga documentation master file, created by
   sphinx-quickstart on Mon Dec 22 16:42:46 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

helga
=====
.. image:: https://img.shields.io/travis/shaunduncan/helga/master.svg
    :target: https://travis-ci.org/shaunduncan/helga

.. image:: https://img.shields.io/coveralls/shaunduncan/helga/master.svg
    :target: https://coveralls.io/r/shaunduncan/helga?branch=master

.. image:: https://img.shields.io/pypi/v/helga.svg
    :target: https://pypi.python.org/pypi/helga

.. image:: https://img.shields.io/pypi/dm/helga.svg
    :target: https://pypi.python.org/pypi/helga


.. _about:

About
-----
Helga is a full-featured chat bot for Python 2.6/2.7 using `Twisted`_. Helga originally started
as a python fork of a perl-based IRC bot `olga`_, but has grown considerably since then. Early
versions limited to support to IRC, but now include other services like XMPP and HipChat.


.. _supported_backends:

Supported Backends
------------------

As of version 1.7.0, helga supports IRC, XMPP, and HipChat out of the box. Note, however, that
helga originally started as an IRC bot, so much of the terminology will reflect that. The current
status of XMPP and HipChat support is very limited and somewhat beta. In the future, helga may
have a much more robust and pluggable backend system to allow connections to any number of chat
services.


.. _features:

Features
--------
* A simple and robust plugin api
* HTTP webhooks support and webhook plugins
* Channel logging and browsable web UI
* Event driven behavior for plugins
* Support for IRC, XMPP, and HipChat


.. _contributing:

Contributing
------------
Contributions are **always** welcomed, whether they be in the form of bug fixes, enhancements,
or just bug reports. To report any issues, please create a ticket on `github`_. For code
changes, please note that any pull request will be denied a merge if the test suite fails.


.. _license:

License
-------
Copyright (c) 2014 Shaun Duncan

Helga is open source software, dual licensed under the MIT and GPL licenses. Dual licensing
was chosen for this project so that plugin authors can create plugins under their choice
of license that is compatible with this project.


Contents
--------
.. toctree::
   :maxdepth: 2

   getting_started 
   configuring_helga
   plugins
   webhooks
   builtins
   api


Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _`Twisted`: https://twistedmatrix.com/trac/
.. _`olga`: https://github.com/thepeopleseason/olga
.. _`github`: https://github.com/shaunduncan/helga/issues
