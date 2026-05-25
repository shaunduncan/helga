"""
Discord communication implementation for Helga bot
"""

import contextlib

try:
    import discord
except ImportError:
    discord = None  # type: ignore[assignment]

import smokesignal
from twisted.internet import reactor

from helga import log, settings
from helga.comm.base import BaseClient
from helga.plugins import registry

logger = log.getLogger(__name__)


class Factory:
    """
    Factory for creating Discord client instances.
    Handles connection lifecycle and auto-reconnect.
    """

    def __init__(self):
        self.client = Client()

    def connect(self):
        """
        Connect to Discord using the bot token from settings.
        """
        token = settings.SERVER.get("TOKEN")
        if not token:
            raise ValueError("Discord TOKEN must be specified in SERVER settings")

        logger.info("Connecting to Discord...")

        # Run the Discord client in a separate thread to avoid blocking Twisted reactor
        import threading

        self.discord_thread = threading.Thread(target=self._run_discord, args=(token,))
        self.discord_thread.daemon = True
        self.discord_thread.start()

    def _run_discord(self, token):
        """
        Run the Discord client in its own event loop.
        """
        try:
            self.client.run(token)
        except Exception as e:
            logger.error("Discord connection failed: %s", e)
            if getattr(settings, "AUTO_RECONNECT", True):
                delay = getattr(settings, "AUTO_RECONNECT_DELAY", 5)
                reactor.callFromThread(reactor.callLater, delay, self.connect)
            else:
                reactor.callFromThread(reactor.stop)


class Client(discord.Client, BaseClient):
    """
    Discord client implementation for Helga.
    Extends discord.Client and BaseClient to provide bot functionality.
    """

    def __init__(self):
        # Initialize Discord client with necessary intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        discord.Client.__init__(self, intents=intents)
        BaseClient.__init__(self)

        self.nickname = settings.NICK
        self._guild_cache = {}
        self._channel_cache = {}
        self._processed_messages = set()

    async def on_ready(self):
        """
        Called when the Discord client has successfully connected.
        Emits the 'signon' signal.
        """
        logger.info("Connected to Discord as %s (ID: %s)", self.user.name, self.user.id)
        self.nickname = self.user.name

        # Cache guilds and channels
        for guild in self.guilds:
            self._guild_cache[guild.id] = guild
            logger.info("Connected to guild: %s (ID: %s)", guild.name, guild.id)

            for channel in guild.text_channels:
                self._channel_cache[channel.id] = channel
                channel_name = f"#{channel.name}"
                self.channels.add(channel_name)

        # Join configured channels (if they exist)
        for channel_config in settings.CHANNELS:
            if isinstance(channel_config, (tuple, list)):
                channel_name = channel_config[0]
            else:
                channel_name = channel_config

            # Discord channels are already "joined" if bot has access
            logger.info("Bot has access to channel: %s", channel_name)

        smokesignal.emit("signon", self)

    async def on_guild_join(self, guild):
        """
        Called when the bot joins a new guild.
        """
        logger.info("Joined guild: %s (ID: %s)", guild.name, guild.id)
        self._guild_cache[guild.id] = guild

        for channel in guild.text_channels:
            self._channel_cache[channel.id] = channel
            channel_name = f"#{channel.name}"
            self.channels.add(channel_name)

    async def on_guild_remove(self, guild):
        """
        Called when the bot is removed from a guild.
        """
        logger.info("Removed from guild: %s (ID: %s)", guild.name, guild.id)
        self._guild_cache.pop(guild.id, None)

        for channel in guild.text_channels:
            self._channel_cache.pop(channel.id, None)
            channel_name = f"#{channel.name}"
            self.channels.discard(channel_name)

    async def on_message(self, message):
        """
        Handler for Discord messages.
        Processes messages through the plugin system.

        :param message: discord.Message object
        """
        # Deduplicate: Discord gateway may send duplicate MESSAGE_CREATE events
        msg_id = message.id
        if msg_id in self._processed_messages:
            return
        self._processed_messages.add(msg_id)
        if len(self._processed_messages) > 1000:
            self._processed_messages.clear()

        # Ignore messages from the bot itself
        if message.author.id == self.user.id:
            return

        # Ignore bot messages if configured
        if message.author.bot:
            return

        user = message.author.name
        content = message.content.strip()

        # Determine channel name
        if isinstance(message.channel, discord.DMChannel):
            # Private message
            channel = user
            is_public = False
        elif isinstance(message.channel, discord.TextChannel):
            # Guild text channel
            channel = f"#{message.channel.name}"
            is_public = True
        else:
            # Other channel types (threads, etc.)
            channel = f"#{message.channel.name}"
            is_public = True

        logger.debug("[<--] %s/%s - %s", channel, user, content)

        # Log channel messages if enabled
        if is_public and settings.CHANNEL_LOGGING:
            self.log_channel_message(channel, user, content)

        # Preprocess the message
        with contextlib.suppress(TypeError, ValueError):
            channel, user, content = registry.preprocess(self, channel, user, content)

        # Process through plugins
        responses = registry.process(self, channel, user, content)

        if responses:
            response_text = "\n".join(responses)
            await self.send_message(message.channel, response_text)

            if is_public and settings.CHANNEL_LOGGING:
                self.log_channel_message(channel, self.nickname, response_text)

        # Update last message
        self.last_message[channel][user] = content

    async def on_member_join(self, member):
        """
        Called when a member joins a guild.
        Emits the 'user_joined' signal for each channel.
        """
        for channel in member.guild.text_channels:
            channel_name = f"#{channel.name}"
            smokesignal.emit("user_joined", self, member.name, channel_name)

    async def on_member_remove(self, member):
        """
        Called when a member leaves a guild.
        Emits the 'user_left' signal for each channel.
        """
        for channel in member.guild.text_channels:
            channel_name = f"#{channel.name}"
            smokesignal.emit("user_left", self, member.name, channel_name)

    def get_channel_logger(self, channel):
        """
        Gets a channel logger for the specified channel.

        :param channel: Channel name (with # prefix)
        :returns: Logger instance
        """
        if channel not in self.channel_loggers:
            self.channel_loggers[channel] = log.get_channel_logger(channel)
        return self.channel_loggers[channel]

    def log_channel_message(self, channel, nick, message):
        """
        Logs a message to the channel logger.

        :param channel: Channel name
        :param nick: User nickname
        :param message: Message content
        """
        if not settings.CHANNEL_LOGGING:
            return
        chan_logger = self.get_channel_logger(channel)
        chan_logger.info(message, extra={"nick": nick})

    async def send_message(self, channel, message):
        """
        Send a message to a Discord channel.

        :param channel: discord.TextChannel, discord.DMChannel, or channel name string
        :param message: Message content to send
        """
        # If channel is a string, find the actual channel object
        if isinstance(channel, str):
            found = self._find_channel(channel)
            if found is None:
                user = self._find_user(channel)
                if user is not None:
                    channel = await user.create_dm()
                else:
                    logger.error("Could not find channel or user: %s", channel)
                    return
            else:
                channel = found

        try:
            # Discord has a 2000 character limit per message
            if len(message) > 2000:
                # Split into multiple messages
                chunks = []
                for i in range(0, len(message), 2000):
                    end = i + 2000
                    chunks.append(message[i:end])
                for chunk in chunks:
                    await channel.send(chunk)
            else:
                await channel.send(message)

            logger.debug(
                "[-->] %s - %s", channel.name if hasattr(channel, "name") else channel, message
            )
        except discord.errors.Forbidden:
            logger.error("No permission to send message to channel: %s", channel)
        except Exception as e:
            logger.error("Failed to send message: %s", e)

    def msg(self, channel, message):
        """
        Send a message (synchronous wrapper for async send_message).
        This is called by plugins and needs to work with Twisted's reactor.

        :param channel: Channel name or discord.TextChannel
        :param message: Message to send
        """
        # Schedule the coroutine to run in the Discord event loop
        import asyncio

        async def _send():
            await self.send_message(channel, message)

        # Get the Discord event loop and schedule the coroutine
        try:
            loop = self.loop
            asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception as e:
            logger.error("Failed to schedule message send: %s", e)

    def me(self, channel, message):
        """
        Send an action message (equivalent to /me in IRC).
        Discord doesn't have native /me support, so we'll format it with italics.

        :param channel: Channel name or discord.TextChannel
        :param message: Action message
        """
        formatted_message = f"*{message}*"
        self.msg(channel, formatted_message)

    def _find_channel(self, channel_name):
        """
        Find a Discord channel by name.

        :param channel_name: Channel name (with or without # prefix)
        :returns: discord.TextChannel or None
        """
        # Remove # prefix if present
        channel_name = channel_name.lstrip("#")

        # Search through cached channels
        for channel in self._channel_cache.values():
            if channel.name == channel_name:
                return channel

        # Search through all guilds
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == channel_name:
                    self._channel_cache[channel.id] = channel
                    return channel

        return None

    def _find_user(self, username):
        """
        Find a Discord user by name.

        :param username: Username to search for
        :returns: discord.User or None
        """
        # Remove @ prefix if present
        username = username.lstrip("@")

        for guild in self.guilds:
            for member in guild.members:
                if member.name == username or member.display_name == username:
                    return member

        return None

    def join(self, channel, key=None):
        """
        Join a channel. In Discord, the bot must be invited to guilds/channels.
        This is a no-op but kept for API compatibility.

        :param channel: Channel name
        :param key: Unused (kept for compatibility)
        """
        logger.info("Discord bots cannot join channels directly - they must be invited")

    def leave(self, channel, reason=None):
        """
        Leave a channel. In Discord, this would mean leaving a guild.
        This is a no-op but kept for API compatibility.

        :param channel: Channel name
        :param reason: Reason for leaving (unused)
        """
        logger.info("Discord bots cannot leave individual channels - only entire guilds")

    def parse_nick(self, full_nick):
        """
        Parse a nickname from a full user string.
        For Discord, this is typically just the username.

        :param full_nick: User identifier
        :returns: Username
        """
        return full_nick

    def is_public_channel(self, channel):
        """
        Check if a channel is public (not a DM).

        :param channel: Channel name
        :returns: True if public channel, False otherwise
        """
        return channel.startswith("#")


# Made with Bob
