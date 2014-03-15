from helga.plugins.webhooks import authenticated, route


@authenticated
@route('/announce/(?P<channel>[\w]+)', methods=['POST'])
def announce(request, irc_client, channel):
    """
    An endpoint for announcing a message on a channel. POST only, must
    provide a single data param 'message'
    """
    if not channel.startswith('#'):
        channel = '#{}'.format(channel)

    message = request.args.get('message', [''])[0]
    if not message:
        request.setResponseCode(400)
        return 'Param message is required'

    irc_client.msg(channel, message)

    # Return accepted
    return 'Message Sent'
