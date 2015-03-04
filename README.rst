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


About
-----
Helga is a full-featured chat bot for Python 2.6/2.7 using `Twisted`_. Helga originally started
as a python fork of a perl-based IRC bot `olga`_, but has grown considerably since then. Early
versions limited to support to IRC, but now include other services like XMPP and HipChat.
Full documentation can be found at http://helga.readthedocs.org.


Supported Backends
------------------

As of version 1.7.0, helga supports IRC, XMPP, and HipChat out of the box. Note, however, that
helga originally started as an IRC bot, so much of the terminology will reflect that. The current
status of XMPP and HipChat support is very limited and somewhat beta. In the future, helga may
have a much more robust and pluggable backend system to allow connections to any number of chat
services.


Contributing
------------
Contributions are **always** welcomed, whether they be in the form of bug fixes, enhancements,
or just bug reports. To report any issues, please create a ticket on `github`_. For code
changes, please note that any pull request will be denied a merge if the test suite fails.

If you are looking to get help with helga, join the #helgabot IRC channel on freenode.


License
-------
Copyright (c) 2014 Shaun Duncan

Helga is open source software, dual licensed under the `MIT`_ and `GPL`_ licenses. Dual licensing
was chosen for this project so that plugin authors can create plugins under their choice
of license that is compatible with this project.

.. _`GPL`: https://github.com/shaunduncan/helga/blob/master/LICENSE-GPL
.. _`MIT`: https://github.com/shaunduncan/helga/blob/master/LICENSE-MIT
.. _`Twisted`: https://twistedmatrix.com/trac/
.. _`olga`: https://github.com/thepeopleseason/olga
.. _`github`: https://github.com/shaunduncan/helga/issues
