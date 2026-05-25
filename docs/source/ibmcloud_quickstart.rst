.. _ibmcloud_quickstart:

IBM Cloud Quick Start
=====================

Deploy Helga to IBM Cloud in 5 minutes!


Prerequisites
-------------

- IBM Cloud account (sign up at https://cloud.ibm.com)
- IBM Cloud CLI installed


Quick Deploy
------------

Option 1: Automated Script (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ./deploy-ibmcloud.sh

The script will guide you through:

1. Creating MongoDB service
2. Configuring IRC settings
3. Deploying to IBM Cloud

Option 2: Manual Deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # 1. Login
    ibmcloud login --sso

    # 2. Target Cloud Foundry
    ibmcloud target --cf -r us-south

    # 3. Create MongoDB
    ibmcloud resource service-instance-create helga-mongodb databases-for-mongodb standard us-south

    # 4. Edit manifest.yml with your IRC settings

    # 5. Deploy
    ibmcloud cf push


Essential Configuration
-----------------------

Edit ``manifest.yml`` and set these environment variables:

.. code-block:: yaml

    env:
      HELGA_IRC_HOST: irc.libera.chat    # Your IRC server
      HELGA_IRC_PORT: 6667                # IRC port
      HELGA_CHANNELS: "#bots,#myroom"     # Channels to join
      HELGA_NICK: helga                   # Bot nickname


Common Commands
---------------

.. code-block:: bash

    # View logs
    ibmcloud cf logs helga-bot

    # Check status
    ibmcloud cf app helga-bot

    # Restart bot
    ibmcloud cf restart helga-bot

    # Set environment variable
    ibmcloud cf set-env helga-bot HELGA_OPERATORS "your_nick"
    ibmcloud cf restage helga-bot


Need Help?
----------

See the complete guide: :doc:`ibmcloud_deployment`


Troubleshooting
---------------

**Bot won't connect?**

- Check logs: ``ibmcloud cf logs helga-bot --recent``
- Verify IRC settings in manifest.yml
- Try enabling SSL: ``HELGA_IRC_SSL: true``

**MongoDB issues?**

- Check service status: ``ibmcloud resource service-instance helga-mongodb``
- Verify service is bound: ``ibmcloud cf services``

**App crashes?**

- Check memory: May need to increase from 512M
- View environment: ``ibmcloud cf env helga-bot``
