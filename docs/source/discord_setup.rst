.. _discord_setup:

Discord Integration
===================

This guide will help you set up Helga to work with Discord.


Prerequisites
-------------

- Python 3.8 or higher
- A Discord account
- Administrator access to a Discord server (or ability to create one)


Step 1: Create a Discord Bot
----------------------------

1. Go to the `Discord Developer Portal <https://discord.com/developers/applications>`_
2. Click "New Application" and give it a name (e.g., "Helga Bot")
3. Navigate to the "Bot" section in the left sidebar
4. Click "Add Bot" and confirm
5. Under the bot's username, click "Reset Token" to reveal your bot token
6. **Important**: Copy this token and keep it secure -- you'll need it for configuration


Step 2: Configure Bot Permissions
---------------------------------

1. In the "Bot" section, scroll down to "Privileged Gateway Intents"
2. Enable the following intents:
   - **Message Content Intent** (required for reading messages)
   - Server Members Intent (optional, for member join/leave events)
   - Presence Intent (optional)


Step 3: Invite Bot to Your Server
---------------------------------

1. Go to the "OAuth2" → "URL Generator" section
2. Under "Scopes", select:
   - ``bot``
3. Under "Bot Permissions", select at minimum:
   - Read Messages/View Channels
   - Send Messages
   - Read Message History
   - Use Slash Commands (optional)
4. Copy the generated URL and open it in your browser
5. Select the server you want to add the bot to and authorize


Step 4: Install Dependencies
----------------------------

.. code-block:: bash

    pip install discord.py>=2.0.0

Or install all Helga dependencies:

.. code-block:: bash

    pip install -r requirements.txt


Step 5: Configure Helga
-----------------------

Create a settings file (e.g., ``discord_settings.py``):

.. code-block:: python

    SERVER = {
        'TYPE': 'discord',
        'TOKEN': 'YOUR_BOT_TOKEN_HERE',  # Replace with your actual token
    }

    NICK = 'helga'

    CHANNELS = [
        '#general',
        '#bots',
    ]

    # Optional: Configure operators (Discord usernames)
    OPERATORS = [
        'your_discord_username',
    ]

    # Optional: Enable plugins
    ENABLED_PLUGINS = True
    DEFAULT_CHANNEL_PLUGINS = True

    # Optional: Command prefix
    COMMAND_PREFIX_CHAR = '!'
    COMMAND_PREFIX_BOTNICK = True


Step 6: Run Helga
-----------------

.. code-block:: bash

    helga --settings=discord_settings.py

Or set the environment variable:

.. code-block:: bash

    export HELGA_SETTINGS=discord_settings.py
    helga


Usage
-----

Once Helga is running and connected to Discord:

Direct Commands
^^^^^^^^^^^^^^^

.. code-block:: none

    !help
    !ping
    helga help

In Channels
^^^^^^^^^^^

The bot will respond to messages in channels it has access to, based on configured plugins.


Important Notes
---------------

Message Content Intent
^^^^^^^^^^^^^^^^^^^^^

Discord requires bots to explicitly request permission to read message content. Make sure you've
enabled the "Message Content Intent" in your bot settings, or Helga won't be able to see messages.

Channel Access
^^^^^^^^^^^^^^

Unlike IRC, Discord bots automatically have access to all channels they have permissions for. The
``CHANNELS`` setting in Helga is informational only -- Discord bots cannot programmatically join or
leave individual channels.

Permissions
^^^^^^^^^^^

Ensure your bot has the necessary permissions in your Discord server:

- View Channels
- Send Messages
- Read Message History
- Embed Links (for rich responses)
- Attach Files (if plugins need to send files)

Rate Limits
^^^^^^^^^^^

Discord has rate limits on API calls. Helga handles this automatically, but be aware that sending
many messages quickly may result in temporary rate limiting.

Message Length
^^^^^^^^^^^^^^

Discord has a 2000 character limit per message. Helga automatically splits longer messages into
multiple parts.


Troubleshooting
---------------

Bot doesn't respond to messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Verify "Message Content Intent" is enabled in Discord Developer Portal
- Check that the bot has "Read Messages" permission in the channel
- Ensure the bot is online (green status in Discord)
- Check Helga logs for errors

Bot can't send messages
^^^^^^^^^^^^^^^^^^^^^^^

- Verify the bot has "Send Messages" permission in the channel
- Check if the channel is read-only for the bot's role

Connection issues
^^^^^^^^^^^^^^^^^

- Verify your bot token is correct
- Check your internet connection
- Review Helga logs for specific error messages


Example Plugins
---------------

Helga's plugin system works the same way with Discord as with IRC. Here are some built-in commands:

- ``!help`` -- Show available commands
- ``!ping`` -- Test if the bot is responsive
- ``!version`` -- Show Helga version


Advanced Configuration
----------------------

For more advanced configuration options, see :doc:`configuring_helga`.

Database Configuration
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    DATABASE = {
        'HOST': 'localhost',
        'PORT': 27017,
        'DB': 'helga',
    }

Logging
^^^^^^^

.. code-block:: python

    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/helga/helga.log'
    CHANNEL_LOGGING = True
    CHANNEL_LOGGING_DIR = '.logs'


Security Best Practices
-----------------------

1. **Never commit your bot token** to version control
2. Use environment variables for sensitive data:

   .. code-block:: python

       import os
       SERVER = {
           'TYPE': 'discord',
           'TOKEN': os.environ.get('DISCORD_BOT_TOKEN'),
       }

3. Regularly rotate your bot token if compromised
4. Use role-based permissions in Discord to limit bot access
5. Configure ``OPERATORS`` to restrict administrative commands


Getting Help
------------

- `Helga Documentation <https://helga.readthedocs.io/>`_
- `Discord.py Documentation <https://discordpy.readthedocs.io/>`_
- `Discord Developer Portal <https://discord.com/developers/docs/>`_


Contributing
------------

Found a bug or want to improve Discord support? Contributions are welcome!
