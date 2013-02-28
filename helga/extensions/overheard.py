from helga.extensions.base import CommandExtension
from helga.util.twitter import tweet, message_max


class OverheadExtension(CommandExtension):
    """
    Command for tweeting out things OH in irc
    """
    usage = '[BOTNICK] tweet_oh <nick>'
    messages = {}

    def record_last(self, channel, nick, message):
        self.messages[channel][nick] = message

    def dispatch(self, nick, channel, message, is_public):
        if channel not in self.messages:
            self.messages[channel] = {}

        opts = self.parse_command(message)

        if not opts or not self.should_handle_message(opts, is_public):
            self.record_last(channel, nick, message)
            return None

        if not is_public:
            return "I can't do that on a private channel"

        return self.handle_message(opts, nick, channel, message, is_public)

    def tweet_oh(self, nick, channel):
        if nick == self.bot.nick:
            return "Nobody needs to know what I say"

        last_message = self.messages[channel].get(nick, '')

        if not last_message:
            return "%s hasn't said anything yet" % nick
        else:
            # Account for 4 characters - OH:<space>
            msg = "OH: %s" % message_max(last_message, 136)
            resp = tweet(msg)

            # No over tweeting
            try:
                del self.messages[channel][nick]
            except KeyError:
                # Hey, we tried
                pass

            if not resp:
                resp = '%(nick)s that probably did not work'

            return resp

    def handle_message(self, opts, nick, channel, message, is_public):
        if opts['tweet_oh']:
            return self.tweet_oh(opts['<nick>'], channel)
