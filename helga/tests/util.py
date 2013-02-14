from mock import Mock


def mock_bot(nick='helga'):
    bot = Mock()
    bot.nick = nick

    return bot
