.. _getting_started:

Getting Started
===============


.. _getting_started.requirements:

Requirements
------------
All python requirements for running helga are listed in ``requirements.txt``. Helga
supports SSL connections to a chat server (currently IRC, XMPP, and HipChat), and for this reason,
you will need to install both ``openssl`` and ``libssl-dev`` in order to compile SSL support.

Optionally, you can have Helga configured to connect to a MongoDB server. Although
this is not strictly required, many plugins require a connection to operate, so it
is highly recommended. "Why MongoDB", you ask? Since MongoDB is a document store,
it is much more flexible for changing schema definitions within plugins. This completely
eliminates the need for Helga to manage schema migrations for different plugin versions.


.. important::

    Helga is currently **only** supported and tested for Python versions 2.6 and 2.7


.. _getting_started.installing:

Installing
----------
Helga is hosted in PyPI. For the latest version, simply install:

.. code-block::bash

    $ pip install helga

Note, that if you follow the development instructions below and wish to install helga in a virtualenv,
you will need to activate it prior to installing helga using pip. In the future, there may be a collection
of .rpm or .deb packages for specific systems, but for now, pip is the only supported means of install.


.. _getting_started.development:

Development Setup
-----------------
To setup helga for development, start by creating a virtualenv and activating it:

.. code-block:: bash

    $ virtualenv helga
    $ cd helga
    $ source bin/activate

Then grab the latest copy of the helga source:

.. code-block:: bash

    $ git clone https://github.com/shaunduncan/helga src/helga
    $ cd src/helga
    $ python setup.py develop

Installing helga this way creates a ``helga`` console script in the virtualenv's ``bin``
directory that will start the helga process. Run it like this:

.. code-block:: bash

    $ helga


.. _getting_started.vagrant:

Using Vagrant
-------------
Alternatively, if you would like to setup helga to run entirely in a virtual machine,
there is a Vagrantfile for you:

.. code-block:: bash

    $ git clone https://github.com/shaunduncan/helga
    $ cd helga
    $ vagrant up

This will provision an ubuntu 12.04 virtual machine with helga fully installed. It will
also ensure that IRC and MongoDB servers are running as well. The VM will have ports
6667 and 27017 for IRC and MongoDB respectively forwarded from the host machine, as well
as private network IP 192.168.10.101. Once this VM is up and running, simply:

.. code-block:: bash

    $ vagrant ssh
    $ helga


.. _getting_started.tests:

Running Tests
-------------
Helga has a full test suite for its various components. Since helga is supported for multiple
python versions, tests are run using `tox`_, which can be run entirely with helga's setup.py.

.. code-block:: bash

    $ python setup.py test

Alternatively, if you would like to run tox directly:

.. code-block:: bash

    $ pip install tox
    $ tox

Helga uses `pytest`_ as it's test runner, so you can run individual tests if you like,
but you will need to install test requirements:

.. code-block:: bash

    $ pip install pytest mock pretend freezegun
    $ py.test


.. _getting_started.docs:

Building Docs
-------------
Much like the test suite, helga's documentation is built using tox:

.. code-block:: bash

    $ tox -e docs

Or alternatively (with installing requirements):

.. code-block:: bash

    $ pip install sphinx alabaster
    $ cd docs
    $ make html


.. _`tox`: https://tox.readthedocs.org/en/latest/
.. _`pytest`: http://pytest.org/latest/
