"""
Tests for Discord communication backend
"""

from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest

from helga.comm import discord as discord_comm


@pytest.fixture
def mock_discord():
    """Mock the discord module"""
    with patch.object(discord_comm, "discord") as mock:
        # Setup mock intents
        mock_intents = Mock()
        mock.Intents.default.return_value = mock_intents
        mock_intents.message_content = True
        mock_intents.members = True
        mock_intents.guilds = True

        # Setup mock channel types
        mock.DMChannel = Mock
        mock.TextChannel = Mock

        # Setup mock errors
        mock.errors.Forbidden = Exception

        yield mock


@pytest.fixture
def client(mock_discord):
    """Create a Discord client instance for testing"""
    with patch.object(discord_comm, "settings") as mock_settings:
        mock_settings.NICK = "helga"
        mock_settings.CHANNELS = ["#bots"]
        mock_settings.CHANNEL_LOGGING = False

        with patch.object(discord_comm.Client, "user", new_callable=PropertyMock) as mock_user:
            mock_user.return_value = Mock()
            mock_user.return_value.name = "helga"
            mock_user.return_value.id = 12345
            with patch.object(
                discord_comm.Client, "guilds", new_callable=PropertyMock
            ) as mock_guilds:
                mock_guilds.return_value = []

                client = discord_comm.Client()
                client.loop = Mock()
                client._mock_guilds = mock_guilds

                yield client


@pytest.fixture
def mock_guild():
    """Create a mock Discord guild"""
    guild = Mock()
    guild.id = 123456789
    guild.name = "Test Guild"
    guild.text_channels = []
    guild.members = []
    return guild


@pytest.fixture
def mock_channel():
    """Create a mock Discord text channel"""
    channel = Mock()
    channel.id = 987654321
    channel.name = "general"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_message(mock_channel):
    """Create a mock Discord message"""
    message = Mock()
    message.author = Mock(name="testuser", bot=False)
    message.content = "Hello, bot!"
    message.channel = mock_channel
    return message


class TestFactory:
    """Tests for Discord Factory"""

    def test_factory_init(self, mock_discord):
        """Test factory initialization"""
        factory = discord_comm.Factory()
        assert factory.client is not None
        assert isinstance(factory.client, discord_comm.Client)

    def test_factory_connect_no_token(self, mock_discord):
        """Test factory connect without token raises error"""
        with patch.object(discord_comm, "settings") as mock_settings:
            mock_settings.SERVER = {}
            factory = discord_comm.Factory()

            with pytest.raises(ValueError, match="Discord TOKEN must be specified"):
                factory.connect()

    def test_factory_connect_with_token(self, mock_discord):
        """Test factory connect with valid token"""
        with patch.object(discord_comm, "settings") as mock_settings:
            mock_settings.SERVER = {"TOKEN": "test_token_123"}
            mock_settings.AUTO_RECONNECT = False

            factory = discord_comm.Factory()

            with patch("threading.Thread") as mock_thread:
                factory.connect()
                mock_thread.assert_called_once()
                assert mock_thread.return_value.daemon is True
                mock_thread.return_value.start.assert_called_once()


class TestClient:
    """Tests for Discord Client"""

    def test_client_init(self, mock_discord):
        """Test client initialization"""
        with patch.object(discord_comm, "settings") as mock_settings:
            mock_settings.NICK = "testbot"

            client = discord_comm.Client()

            assert client.nickname == "testbot"
            assert client._guild_cache == {}
            assert client._channel_cache == {}

    @pytest.mark.asyncio
    async def test_on_ready(self, client, mock_guild, mock_channel):
        """Test on_ready event handler"""
        mock_guild.text_channels = [mock_channel]
        client._mock_guilds.return_value = [mock_guild]

        with patch.object(discord_comm, "smokesignal") as mock_signal:
            await client.on_ready()

            assert client.nickname == "helga"
            assert mock_guild.id in client._guild_cache
            assert mock_channel.id in client._channel_cache
            assert "#general" in client.channels
            mock_signal.emit.assert_called_with("signon", client)

    @pytest.mark.asyncio
    async def test_on_guild_join(self, client, mock_guild, mock_channel):
        """Test on_guild_join event handler"""
        mock_guild.text_channels = [mock_channel]

        await client.on_guild_join(mock_guild)

        assert mock_guild.id in client._guild_cache
        assert mock_channel.id in client._channel_cache
        assert "#general" in client.channels

    @pytest.mark.asyncio
    async def test_on_guild_remove(self, client, mock_guild, mock_channel):
        """Test on_guild_remove event handler"""
        mock_guild.text_channels = [mock_channel]
        client._guild_cache[mock_guild.id] = mock_guild
        client._channel_cache[mock_channel.id] = mock_channel
        client.channels.add("#general")

        await client.on_guild_remove(mock_guild)

        assert mock_guild.id not in client._guild_cache
        assert mock_channel.id not in client._channel_cache
        assert "#general" not in client.channels

    @pytest.mark.asyncio
    async def test_on_message_ignores_self(self, client, mock_message):
        """Test that bot ignores its own messages"""
        mock_message.author = client.user

        with patch.object(discord_comm.registry, "process") as mock_process:
            await client.on_message(mock_message)
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_ignores_bots(self, client, mock_message):
        """Test that bot ignores other bot messages"""
        mock_message.author.bot = True

        with patch.object(discord_comm.registry, "process") as mock_process:
            await client.on_message(mock_message)
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_processes_user_message(self, client, mock_message, mock_channel):
        """Test processing of user messages"""
        mock_message.channel = mock_channel

        with patch.object(discord_comm.registry, "process", return_value=None) as mock_process:
            with patch.object(
                discord_comm.registry,
                "preprocess",
                return_value=("#general", "testuser", "Hello, bot!"),
            ):
                await client.on_message(mock_message)

                mock_process.assert_called_once()
                call_args = mock_process.call_args[0]
                assert call_args[0] == client
                assert call_args[1] == "#general"
                assert call_args[2] == "testuser"
                assert call_args[3] == "Hello, bot!"

    @pytest.mark.asyncio
    async def test_on_message_sends_response(self, client, mock_message, mock_channel):
        """Test that responses are sent back"""
        mock_message.channel = mock_channel

        with patch.object(
            discord_comm.registry, "process", return_value=["Response 1", "Response 2"]
        ):
            with patch.object(
                discord_comm.registry,
                "preprocess",
                return_value=("#general", "testuser", "Hello, bot!"),
            ):
                with patch.object(client, "send_message", new_callable=AsyncMock) as mock_send:
                    await client.on_message(mock_message)

                    mock_send.assert_called_once_with(mock_channel, "Response 1\nResponse 2")

    @pytest.mark.asyncio
    async def test_on_message_dm_channel(self, client, mock_message):
        """Test handling of direct messages"""
        dm_channel = Mock()
        dm_channel.name = "DM"
        mock_message.channel = dm_channel

        with patch.object(discord_comm.registry, "process", Mock(return_value=None)):
            with patch.object(
                discord_comm.registry,
                "preprocess",
                Mock(return_value=("testuser", "testuser", "Hello!")),
            ):
                await client.on_message(mock_message)

                # Verify last_message was updated with user as channel
                assert "testuser" in client.last_message

    @pytest.mark.asyncio
    async def test_send_message_short(self, client, mock_channel):
        """Test sending a short message"""
        await client.send_message(mock_channel, "Short message")

        mock_channel.send.assert_called_once_with("Short message")

    @pytest.mark.asyncio
    async def test_send_message_long(self, client, mock_channel):
        """Test sending a message longer than 2000 characters"""
        long_message = "A" * 2500

        await client.send_message(mock_channel, long_message)

        # Should be called twice (2000 + 500 characters)
        assert mock_channel.send.call_count == 2

    @pytest.mark.asyncio
    async def test_send_message_by_name(self, client, mock_channel):
        """Test sending message by channel name"""
        client._channel_cache[mock_channel.id] = mock_channel

        with patch.object(client, "_find_channel", return_value=mock_channel):
            await client.send_message("#general", "Test message")

            mock_channel.send.assert_called_once_with("Test message")

    def test_msg_schedules_async_send(self, client, mock_channel):
        """Test that msg() schedules async send"""

        with patch("asyncio.run_coroutine_threadsafe") as mock_run:
            client.msg(mock_channel, "Test")
            mock_run.assert_called_once()

    def test_me_formats_with_italics(self, client, mock_channel):
        """Test that me() formats message with italics"""
        with patch.object(client, "msg") as mock_msg:
            client.me(mock_channel, "waves")
            mock_msg.assert_called_once_with(mock_channel, "*waves*")

    def test_find_channel_by_name(self, client, mock_channel):
        """Test finding channel by name"""
        client._channel_cache[mock_channel.id] = mock_channel

        result = client._find_channel("general")
        assert result == mock_channel

        result = client._find_channel("#general")
        assert result == mock_channel

    def test_find_channel_not_found(self, client):
        """Test finding non-existent channel"""
        result = client._find_channel("nonexistent")
        assert result is None

    def test_find_user_by_name(self, client, mock_guild):
        """Test finding user by name"""
        mock_member = Mock(display_name="Test User")
        mock_member.name = "testuser"
        mock_guild.members = [mock_member]
        client._mock_guilds.return_value = [mock_guild]

        result = client._find_user("testuser")
        assert result == mock_member

        result = client._find_user("@testuser")
        assert result == mock_member

    def test_find_user_not_found(self, client):
        """Test finding non-existent user"""
        result = client._find_user("nonexistent")
        assert result is None

    def test_parse_nick(self, client):
        """Test parse_nick returns the input"""
        assert client.parse_nick("testuser") == "testuser"

    def test_is_public_channel(self, client):
        """Test is_public_channel detection"""
        assert client.is_public_channel("#general") is True
        assert client.is_public_channel("general") is False
        assert client.is_public_channel("username") is False

    def test_join_is_noop(self, client):
        """Test that join is a no-op for Discord"""
        # Should not raise an error
        client.join("#test")

    def test_leave_is_noop(self, client):
        """Test that leave is a no-op for Discord"""
        # Should not raise an error
        client.leave("#test")

    @pytest.mark.asyncio
    async def test_on_member_join(self, client, mock_guild, mock_channel):
        """Test on_member_join event handler"""
        mock_member = Mock()
        mock_member.name = "newuser"
        mock_guild.text_channels = [mock_channel]
        mock_member.guild = mock_guild

        with patch.object(discord_comm, "smokesignal") as mock_signal:
            await client.on_member_join(mock_member)

            mock_signal.emit.assert_called_with("user_joined", client, "newuser", "#general")

    @pytest.mark.asyncio
    async def test_on_member_remove(self, client, mock_guild, mock_channel):
        """Test on_member_remove event handler"""
        mock_member = Mock()
        mock_member.name = "olduser"
        mock_guild.text_channels = [mock_channel]
        mock_member.guild = mock_guild

        with patch.object(discord_comm, "smokesignal") as mock_signal:
            await client.on_member_remove(mock_member)

            mock_signal.emit.assert_called_with("user_left", client, "olduser", "#general")

    def test_get_channel_logger(self, client):
        """Test getting channel logger"""
        with patch.object(discord_comm.log, "get_channel_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = client.get_channel_logger("#test")

            assert result == mock_logger
            assert "#test" in client.channel_loggers
            mock_get_logger.assert_called_once_with("#test")

    def test_log_channel_message_disabled(self, client):
        """Test that logging is skipped when disabled"""
        with patch.object(discord_comm, "settings") as mock_settings:
            mock_settings.CHANNEL_LOGGING = False

            with patch.object(client, "get_channel_logger") as mock_get_logger:
                client.log_channel_message("#test", "user", "message")
                mock_get_logger.assert_not_called()

    def test_log_channel_message_enabled(self, client):
        """Test that logging works when enabled"""
        with patch.object(discord_comm, "settings") as mock_settings:
            mock_settings.CHANNEL_LOGGING = True

            mock_logger = Mock()
            with patch.object(client, "get_channel_logger", return_value=mock_logger):
                client.log_channel_message("#test", "user", "message")

                mock_logger.info.assert_called_once_with("message", extra={"nick": "user"})


# Made with Bob
