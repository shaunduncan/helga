"""
Example Discord configuration for Helga bot

To use this configuration:
1. Create a Discord bot at https://discord.com/developers/applications
2. Copy your bot token
3. Enable "Message Content Intent" in the bot settings
4. Invite the bot to your server
5. Run: helga --settings=settings_discord_example.py
"""

# Discord server configuration
SERVER = {
    "TYPE": "discord",
    "TOKEN": "YOUR_BOT_TOKEN_HERE",  # Replace with your actual bot token
}

# Bot nickname (optional, Discord will use the bot's configured name)
NICK = "helga"

# Channels to monitor (Discord bots have access to all channels they have permissions for)
# This setting is informational - Discord bots cannot programmatically join channels
CHANNELS = [
    "#general",
    "#bots",
]

# MongoDB configuration (optional, for plugins that need persistence)
DATABASE = {
    "HOST": "localhost",
    "PORT": 27017,
    "DB": "helga",
}

# Enable channel logging (optional)
CHANNEL_LOGGING = False
CHANNEL_LOGGING_DIR = ".logs"

# Bot operators (Discord usernames)
OPERATORS = [
    "your_username",
]

# Plugin configuration
ENABLED_PLUGINS = True  # Enable all installed plugins
DEFAULT_CHANNEL_PLUGINS = True  # Enable plugins on all channels by default

# Command prefix
COMMAND_PREFIX_CHAR = "!"  # Commands can be invoked with !command
COMMAND_PREFIX_BOTNICK = True  # Commands can be invoked with helga command

# Auto-reconnect settings
AUTO_RECONNECT = True
AUTO_RECONNECT_DELAY = 5

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = None  # None means log to stdout

# Made with Bob
