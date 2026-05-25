.. _ibmcloud_deployment:

Deploying Helga to IBM Cloud
============================

This guide will walk you through deploying the Helga IRC bot to IBM Cloud using Cloud Foundry.


Prerequisites
-------------

1. **IBM Cloud Account**: Sign up at https://cloud.ibm.com
2. **IBM Cloud CLI**: Install from https://cloud.ibm.com/docs/cli
3. **Cloud Foundry CLI**: Usually included with IBM Cloud CLI
4. **IRC Server Access**: You'll need access to an IRC server (e.g., Freenode, Libera.Chat)


Step 1: Install IBM Cloud CLI
-----------------------------

.. code-block:: bash

    # For Linux/macOS
    curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

    # For Windows, download from:
    # https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli


Step 2: Login to IBM Cloud
--------------------------

.. code-block:: bash

    ibmcloud login

If you have a federated ID:

.. code-block:: bash

    ibmcloud login --sso


Step 3: Target Cloud Foundry
----------------------------

.. code-block:: bash

    # List available regions
    ibmcloud regions

    # Target a region (e.g., us-south)
    ibmcloud target --cf -r us-south

    # Or target a specific org and space
    ibmcloud target -o YOUR_ORG -s YOUR_SPACE


Step 4: Create MongoDB Service
------------------------------

Helga requires MongoDB for storing data. Create a MongoDB service instance:

.. code-block:: bash

    # Option 1: Databases for MongoDB (recommended)
    ibmcloud resource service-instance-create helga-mongodb databases-for-mongodb standard us-south

    # Option 2: Compose for MongoDB (legacy)
    ibmcloud cf create-service compose-for-mongodb Standard helga-mongodb

Wait for the service to be provisioned (this may take several minutes):

.. code-block:: bash

    ibmcloud resource service-instance helga-mongodb


Step 5: Configure Environment Variables
---------------------------------------

Before deploying, you need to set up your IRC server configuration:

Option A: Edit manifest.yml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit the ``manifest.yml`` file and add your configuration under the ``env`` section:

.. code-block:: yaml

    env:
      PYTHONUNBUFFERED: true
      HELGA_NICK: helga
      HELGA_LOG_LEVEL: INFO
      HELGA_IRC_HOST: irc.libera.chat
      HELGA_IRC_PORT: 6667
      HELGA_IRC_SSL: false
      HELGA_CHANNELS: "#bots,#helga-dev"
      HELGA_OPERATORS: "your_nick,another_nick"

Option B: Set via CLI (after deployment)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ibmcloud cf set-env helga-bot HELGA_IRC_HOST irc.libera.chat
    ibmcloud cf set-env helga-bot HELGA_IRC_PORT 6667
    ibmcloud cf set-env helga-bot HELGA_CHANNELS "#bots,#helga-dev"
    ibmcloud cf restage helga-bot


Step 6: Deploy to IBM Cloud
---------------------------

From the helga project root directory:

.. code-block:: bash

    # Deploy the application
    ibmcloud cf push

The deployment process will:

1. Upload your application code
2. Install Python dependencies from requirements.txt
3. Bind the MongoDB service
4. Start the Helga bot


Step 7: Monitor Your Deployment
-------------------------------

.. code-block:: bash

    # Check application status
    ibmcloud cf app helga-bot

    # View logs
    ibmcloud cf logs helga-bot --recent

    # Stream logs in real-time
    ibmcloud cf logs helga-bot


Configuration Options
---------------------

All configuration is done via environment variables.

Required Settings
^^^^^^^^^^^^^^^^^

- ``HELGA_IRC_HOST``: IRC server hostname (e.g., irc.libera.chat)
- ``HELGA_IRC_PORT``: IRC server port (default: 6667)
- ``HELGA_CHANNELS``: Comma-separated list of channels to join (e.g., "#bots,#helga")

Optional Settings
^^^^^^^^^^^^^^^^^

- ``HELGA_NICK``: Bot nickname (default: helga)
- ``HELGA_IRC_SSL``: Use SSL connection (true/false, default: false)
- ``HELGA_IRC_USERNAME``: IRC username for authentication
- ``HELGA_IRC_PASSWORD``: IRC password for authentication
- ``HELGA_OPERATORS``: Comma-separated list of operator nicks
- ``HELGA_LOG_LEVEL``: Logging level (DEBUG, INFO, WARNING, ERROR)
- ``HELGA_COMMAND_PREFIX``: Command prefix character (default: !)
- ``HELGA_CHANNEL_LOGGING``: Enable channel logging (true/false)
- ``HELGA_WEBHOOK_USER``: Username for webhook authentication
- ``HELGA_WEBHOOK_PASS``: Password for webhook authentication

MongoDB Settings (if not using IBM Cloud service)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``HELGA_MONGO_HOST``: MongoDB hostname
- ``HELGA_MONGO_PORT``: MongoDB port (default: 27017)
- ``HELGA_MONGO_DB``: Database name (default: helga)
- ``HELGA_MONGO_USERNAME``: MongoDB username
- ``HELGA_MONGO_PASSWORD``: MongoDB password


Updating Your Deployment
------------------------

.. code-block:: bash

    # Push updates
    ibmcloud cf push

    # Or if you only changed environment variables
    ibmcloud cf restage helga-bot


Scaling
-------

.. code-block:: bash

    # Change memory allocation
    ibmcloud cf scale helga-bot -m 1G

    # Change number of instances (not recommended for IRC bots)
    ibmcloud cf scale helga-bot -i 1


Troubleshooting
---------------

Bot won't connect to IRC
^^^^^^^^^^^^^^^^^^^^^^^^

1. Check logs: ``ibmcloud cf logs helga-bot --recent``
2. Verify IRC server settings are correct
3. Check if IRC server requires SSL: set ``HELGA_IRC_SSL=true``
4. Some IRC servers require authentication

MongoDB connection issues
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Verify service is bound: ``ibmcloud cf services``
2. Check service credentials: ``ibmcloud cf env helga-bot``
3. Ensure MongoDB service is fully provisioned

Application crashes on startup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Check logs for Python errors
2. Verify all required dependencies are in requirements.txt
3. Check memory allocation (may need to increase)

View environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ibmcloud cf env helga-bot


Stopping/Starting the Bot
-------------------------

.. code-block:: bash

    # Stop the bot
    ibmcloud cf stop helga-bot

    # Start the bot
    ibmcloud cf start helga-bot

    # Restart the bot
    ibmcloud cf restart helga-bot


Deleting the Deployment
-----------------------

.. code-block:: bash

    # Delete the application
    ibmcloud cf delete helga-bot

    # Delete the MongoDB service (WARNING: This deletes all data)
    ibmcloud resource service-instance-delete helga-mongodb


Cost Considerations
-------------------

- **Cloud Foundry Runtime**: Free tier includes 256MB of memory. Helga uses 512MB by default.
- **Databases for MongoDB**: Starts at ~$60/month for Standard plan
- **Compose for MongoDB**: Legacy service, pricing varies

Consider using the IBM Cloud free tier for testing, but be aware of limitations.


Security Best Practices
-----------------------

1. **Never commit credentials**: Use environment variables for all sensitive data
2. **Use webhook authentication**: Set ``HELGA_WEBHOOK_USER`` and ``HELGA_WEBHOOK_PASS``
3. **Limit operators**: Only add trusted users to ``HELGA_OPERATORS``
4. **Use SSL**: Enable ``HELGA_IRC_SSL=true`` when possible
5. **Regular updates**: Keep dependencies updated for security patches


Additional Resources
--------------------

- `IBM Cloud Documentation <https://cloud.ibm.com/docs>`_
- `Cloud Foundry Documentation <https://docs.cloudfoundry.org/>`_
- `Helga Documentation <http://helga.readthedocs.org>`_
- `Helga GitHub Repository <https://github.com/shaunduncan/helga>`_


Support
-------

For issues specific to:

- **IBM Cloud**: https://cloud.ibm.com/docs/get-support
- **Helga Bot**: https://github.com/shaunduncan/helga/issues
- **IRC Help**: Join #helgabot on Freenode


Example: Complete Deployment
----------------------------

Here's a complete example from start to finish:

.. code-block:: bash

    # 1. Login to IBM Cloud
    ibmcloud login --sso

    # 2. Target Cloud Foundry
    ibmcloud target --cf -r us-south

    # 3. Create MongoDB service
    ibmcloud resource service-instance-create helga-mongodb databases-for-mongodb standard us-south

    # 4. Wait for service to be ready (check status)
    ibmcloud resource service-instance helga-mongodb

    # 5. Edit manifest.yml with your IRC settings
    # (or set environment variables after deployment)

    # 6. Deploy
    ibmcloud cf push

    # 7. Watch logs
    ibmcloud cf logs helga-bot

    # 8. Set additional environment variables if needed
    ibmcloud cf set-env helga-bot HELGA_OPERATORS "your_nick"
    ibmcloud cf restage helga-bot

Your Helga bot should now be running on IBM Cloud and connected to your IRC server!
