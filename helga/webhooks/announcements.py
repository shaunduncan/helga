from helga import log
from helga.plugins.webhooks import authenticated, route


logger = log.getLogger(__name__)


@route('/announce/(?P<channel>[\w\-_]+)', methods=['POST'])
@authenticated
def announce(request, irc_client, channel):
    """
    An endpoint for announcing a message on a channel. POST only, must
    provide a single data param 'message'
    """
    if not channel.startswith('#'):
        channel = '#{0}'.format(channel)

    message = request.args.get('message', [''])[0]
    if not message:
        request.setResponseCode(400)
        return 'Param message is required'

    logger.info('Sending message to %s: "%s"', channel, message)
    irc_client.msg(channel, message)

    # Return accepted
    return 'Message Sent'
